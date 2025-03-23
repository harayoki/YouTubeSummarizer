# YouTube Summarizer

YouTube動画から自動字幕を取得し、チャプターごとに整形・要約してMarkdownファイルとして保存するツールです。

## 特徴

- 自動字幕の取得（`YouTubeTranscriptApi`使用）
- 説明欄からチャプター情報を自動抽出
- チャプターごとの文字起こし出力（時刻付き）
- OpenAI API（GPT-3.5）による日本語要約（オプション）
- Markdown形式で出力
- ファイル名はYouTube動画タイトルに自動設定

YoutubeAPIは利用しません。チャプターの情報を取るのに説明欄のテキストを利用するため、
説明欄にチャプター情報がない場合はチャプターが一つとしてある買われます。

## 動作環境

開発はPython 3.13.0 / Windows 11 で行っています。
仮想環境を作成し、以下のコマンドでモジュールをインストールしてください。

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python src/main.py URL [-o 出力先ディレクトリ] [-l 言語コード] [--summarize]
```

### 引数

- `URL` : 対象のYouTube動画URL
- `-o` : 出力ディレクトリ（指定しない場合は標準出力）
- `-l` : 言語コード（例：`en`、`ja`）。省略時は自動選択
- `--summarize` : チャプターごとにOpenAI APIで要約を追加（要APIキー）

### 例

```bash
# 要約なし、標準出力
python src/main.py "https://www.youtube.com/watch?v=xxxx"

# 要約あり、Markdownを指定ディレクトリに保存
python src/main.py "https://www.youtube.com/watch?v=xxxx" -o out -sm

# 実例 Blender4.4 リリース告知動画
python src/main.py "https://www.youtube.com/watch?v=-eqPs-boihU" -l en -o out -sm
```

## 注意点：長時間動画の要約について

要約機能（--summarize）では 動画が長いほどトークン使用量が増えます 。
OpenAI APIは 入力・出力トークンの合計に応じて従量課金されます。 
チャプターが多い、または字幕が長い動画ではコストが高くなる場合があります。

## OpenAI APIキーの設定

要約を行うには、環境変数 `OPENAI_API_KEY` にAPIキーを設定してください。

```bash
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

Windowsの場合：

```powershell
$env:OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxx"
```

## 出力例

```
# 動画タイトル
[動画URL]

## 要約
動画全体の要約

###  チャプター1: タイトル (00:00:00 〜 00:mm:ss)
チャプター１翻訳

### チャプター2: タイトル (00:mm:ss 〜 00:mm:ss)
小さめのフライパンに肉だを入れ、広げて焼く。ガイドラインを入れて焼く深さの目安を示す。ひっくり返して切り分ける。
チャプター2翻訳

### チャプター3: タイトル (00:mm:ss 〜 00:mm:ss)
最後におすすめのタレを2種類紹介。
チャプター3翻訳

：
：

---

## チャプター1: タイトル
**時間**: 00:00:00 〜 00:mm:nn

- [00:00:00] 文字おこし
- [00:mm:nn] 文字おこし
- [00:mm:nn] 文字おこし
- [00:mm:nn] 文字おこし
- [00:mm:nn] 文字おこし

## チャプター2: タイトル
**時間**: 00:mm:nn 〜 00:mm:nn

- [00:mm:nn] 文字おこし
- [00:mm:nn] 文字おこし
- [00:mm:nn] 文字おこし
- [00:mm:nn] 文字おこし
- [00:mm:nn] 文字おこし

：
：
```

## ライセンス

MIT License となります。




