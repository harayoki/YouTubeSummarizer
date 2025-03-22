# YouTube Summarizer

YouTube動画から自動字幕を取得し、チャプターごとに整形・要約してMarkdownファイルとして保存するツールです。

## 特徴

- 自動字幕の取得（`YouTubeTranscriptApi`使用）
- 説明欄からチャプター情報を自動抽出
- チャプターごとの文字起こし出力（時刻付き）
- OpenAI API（GPT-3.5）による日本語要約（オプション）
- Markdown形式で出力
- ファイル名はYouTube動画タイトルに自動設定

## インストール

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
python src/main.py "https://www.youtube.com/watch?v=xxxx" -o out --summarize
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
## チャプタータイトル
**時間**: 00:03:15 〜 00:07:42

- [00:03:15] 字幕テキスト
- [00:03:45] 字幕テキスト
...

---

## 要約（チャプターごと）
- チャプター1（00:00:00 〜 00:03:15）: 概要...
- チャプター2（00:03:15 〜 00:07:42）: 概要...
```

## ライセンス

[LICENSE](LICENSE)

