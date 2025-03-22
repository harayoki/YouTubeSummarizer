import argparse
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs
import urllib.request
import re
import openai
import os
import pathlib
import sys


def get_video_id(url):
    query = urlparse(url)
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        return parse_qs(query.query).get('v', [None])[0]
    elif query.hostname == 'youtu.be':
        return query.path.lstrip('/')
    return None


def get_video_title(video_url):
    try:
        response = urllib.request.urlopen(video_url)
        html = response.read().decode('utf-8')
        title_match = re.search(r'<title>(.*?)</title>', html)
        if title_match:
            return title_match.group(1).replace(" - YouTube", "").strip()
    except Exception:
        pass
    return "output"


def parse_chapters(video_url):
    try:
        response = urllib.request.urlopen(video_url)
        html = response.read().decode('utf-8')

        desc_match = re.search(r'"shortDescription":"(.*?)"', html, re.DOTALL)
        if desc_match:
            description = desc_match.group(1).encode('utf-8').decode('unicode_escape')
        else:
            description = ''
    except Exception as e:
        print(f"チャプター取得失敗（HTML取得エラー）: {e}")
        return [{"start": 0, "title": "全体"}, {"start": float("inf"), "title": "END"}]

    pattern = re.compile(r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s+(?P<title>.+)")
    chapters = []
    for match in pattern.finditer(description):
        time_str = match.group("time")
        title = match.group("title").strip()
        parts = list(map(int, time_str.split(":")))
        if len(parts) == 2:
            seconds = parts[0] * 60 + parts[1]
        else:
            seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
        chapters.append({"start": seconds, "title": title})

    if not chapters:
        chapters.append({"start": 0, "title": "全体"})
    chapters.append({"start": float("inf"), "title": "END"})
    return chapters


def resolve_language_preference(args_langs, transcript_list):
    if args_langs:
        try:
            transcript_list.find_transcript(args_langs)
            return args_langs
        except NoTranscriptFound:
            print(f"警告: 指定された言語 {args_langs} の字幕が見つかりません。自動選択に切り替えます。")

    all_transcripts = transcript_list._manually_created_transcripts or transcript_list._generated_transcripts
    first = next(iter(all_transcripts), None)
    if isinstance(first, str):
        return [first]
    elif hasattr(first, 'language_code'):
        return [first.language_code]
    return []


def fetch_transcript(video_url, languages):
    video_id = get_video_id(video_url)
    if not video_id:
        raise ValueError("無効なURLです")

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        print("取得可能な字幕一覧：")
        for transcript in transcript_list:
            print(f"- {transcript.language_code} ({'auto' if transcript.is_generated else 'manual'})")

        languages = resolve_language_preference(languages, transcript_list)
        return transcript_list.find_transcript(languages).fetch()

    except TranscriptsDisabled:
        raise RuntimeError("この動画では字幕（自動含む）が無効です")
    except NoTranscriptFound:
        raise RuntimeError("指定された言語の字幕が見つかりません")
    except Exception as e:
        raise RuntimeError(f"字幕取得に失敗: {e}")


def group_transcript_by_chapters(transcript, chapters):
    grouped = []
    for i in range(len(chapters) - 1):
        start_time = chapters[i]['start']
        end_time = chapters[i + 1]['start']
        title = chapters[i]['title']

        entries = [
            entry for entry in transcript
            if start_time <= entry['start'] < end_time
        ]
        grouped.append({
            "title": title,
            "start": start_time,
            "end": end_time,
            "entries": entries
        })
    return grouped


def seconds_to_timestamp(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def summarize_chapters_bulk(chapters):
    prompt = ("以下はYouTube動画の各チャプターの内容です。全体の要約を最大600文字程度で日本語にしてください。またそれに続いて、"
              "それぞれのチャプターについて個別に、タイトルと時間情報を含めて読みやすく成形された日本語で"
              "最大200文字程度で翻訳してください。\n")
    for chapter in chapters:
        prompt += f"\n## {chapter['title']} ({chapter['start_ts']} 〜 {chapter['end_ts']})\n{chapter['text']}\n"

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたは日本語で翻訳や要約を行うアシスタントです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=1500
    )
    return response.choices[0].message.content.strip()


def render_chaptered_transcript_md(grouped_chapters, do_summarize=False):
    lines = []
    full_chapters = []

    for chapter in grouped_chapters:
        title = chapter["title"]
        start = chapter["start"]
        end = chapter["end"]
        entries = chapter["entries"]

        start_ts = seconds_to_timestamp(start)
        end_ts = seconds_to_timestamp(end) if end != float("inf") else "END"

        lines.append(f"## {title}")
        lines.append(f"**時間**: {start_ts} 〜 {end_ts}\n")

        full_text = ""
        for entry in entries:
            ts = seconds_to_timestamp(entry['start'])
            text = entry['text'].replace('\n', ' ')
            lines.append(f"- [{ts}] {text}")
            full_text += text + " "

        full_chapters.append({
            "title": title,
            "start_ts": start_ts,
            "end_ts": end_ts,
            "text": full_text.strip()
        })

    if do_summarize:
        summary_text = summarize_chapters_bulk(full_chapters)
        lines.append("\n---\n")
        lines.append("## 要約（チャプターごと）")
        lines.append(summary_text)

    return "\n".join(lines)


def resolve_output_path(output_arg, title):
    path = pathlib.Path(output_arg)
    if path.suffix:
        path = path.parent
    if not path.exists():
        print(f"エラー: 出力先ディレクトリが存在しません: {path}")
        sys.exit(1)
    return path / f"{title}.md"


def main():
    parser = argparse.ArgumentParser(description="YouTube字幕をチャプターごとにMarkdown出力")
    parser.add_argument("url", help="YouTube動画のURL")
    parser.add_argument("-o", "--output_dir", help="出力先ディレクトリ")
    parser.add_argument("-l", "--language", help="優先言語: ja / en など")
    parser.add_argument("-sm", "--summarize", action="store_true", help="各チャプターの要約を付加する")
    args = parser.parse_args()

    if args.summarize and not os.getenv("OPENAI_API_KEY"):
        print("エラー: 要約を有効にするには 環境変数に OPENAI_API_KEY を設定してください")
        return

    if args.output_dir:
        # ディレクトリ存在チェック
        _ = resolve_output_path(args.output_dir, "test")

    try:
        print(">>> 字幕取得中...")
        transcript = fetch_transcript(args.url, [args.language])

        print(">>> チャプター解析中...")
        chapters = parse_chapters(args.url)

        print(">>> チャプターごとの分類中...")
        grouped = group_transcript_by_chapters(transcript, chapters)

        print(">>> Markdown整形中...")
        md_text = render_chaptered_transcript_md(grouped, do_summarize=args.summarize)

        if args.output_dir:
            title = get_video_title(args.url)
            filename = resolve_output_path(args.output_dir, title)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(md_text)
            print(f"保存しました: {filename}")
        else:
            print(md_text)
    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    main()
