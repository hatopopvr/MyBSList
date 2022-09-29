# MyBSList

ScoreSaberから取得した内容に基づいて星別のプレイリストを作成するスクリプトです.

## 適用範囲
本プログラムは以下の環境でのみ動作を確認しています。
- Windows 10 pro 64bit
- Python 3.7.9

## 使い方

### 導入

python導入済とします。
```
pip install -r requirements.txt
```

### 設定

`config.ini`を開き、以下を自分の環境に合わせて設定ください。  
Playlistsディレクトリは `[Beat Saberインストールディレクトリ]\Playlists` にあります。

```config.ini
[param]
# ScoreSaberのPlayerID。変更必須。
player_id = 76561198412839195

# BeatSaberプレイリストのフォルダ
playlist_dir = C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Playlists
```

星毎に以下の条件を設定してください。
```config.ini
[star00]
playlist_is_enable = True
not_play_is_enable = True
nf_is_enable = True
not_fc_is_enable = False
filtered_is_enable = True
filtered_pp_min = 0
filtered_pp_max = 1000
filtered_acc_min = 0
filtered_acc_max = 99
filtered_miss_min = 0
filtered_miss_max = 10000
filtered_rank_min = 1000
filtered_rank_max = 999999
```

### 実行

`app.bat`をダブルクリックで実行ください。
実行すると、consoleに以下のような内容が出力されておれば、正常に完了しています。

```
D:\PythonProgram\MyBSTasks>python MyBSList.py
2022-09-29 18:55:23,522 -     INFO - ---------------------------------
2022-09-29 18:55:23,522 -     INFO - 作業を開始します.
2022-09-29 18:55:23,523 -     INFO - 作業ディレクトリを作成します.
2022-09-29 18:55:23,523 -     INFO - 作業ディレクトリの作成が完了しました. path:work
2022-09-29 18:55:23,523 -     INFO - プレイヤー情報を取得します.
2022-09-29 18:55:24,055 -     INFO - Player情報の取得が完了しました. hatopop, 総プレイ数:3,064, ランク譜面プレイ数:2,830, ページ数:32
2022-09-29 18:55:24,055 -     INFO - ランク譜面のデータを取得します.
2022-09-29 18:55:27,139 -     INFO - ランク譜面のデータ取得が完了しました. path:work\outcome.csv, count:3420
2022-09-29 18:55:27,139 -     INFO - LeaderBoardからランク譜面数を照合します.
2022-09-29 18:55:27,550 -     INFO - LeaderBoardのランク譜面数は 3,420 です.
2022-09-29 18:55:27,552 -     INFO - ランク譜面数が一致しました.再取得処理を完了します.
2022-09-29 18:55:27,553 -     INFO - PlayerのScore情報を取得します.
2022-09-29 18:55:29,295 -     INFO - PlayerのScore情報を取得を完了しました. ランク譜面プレイ数は 2,830 です.
2022-09-29 18:55:29,297 -     INFO - notes数とcombo数に基づきAccの再計算を開始します.
2022-09-29 18:55:29,307 -     INFO - Accがゲームと異なる結果が42件あります.
2022-09-29 18:55:29,308 -     INFO - Accを再計算した結果を上書きしました.
2022-09-29 18:55:29,308 -     INFO - 結合データを作成します.
2022-09-29 18:55:29,366 -     INFO - 結合が完了しました.件数:3,420
2022-09-29 18:55:29,366 -     INFO - 作業ディレクトリのPlaylistを削除します.
2022-09-29 18:55:29,367 -     INFO - 作業ディレクトリのPlaylist削除が完了しました. 10 件
2022-09-29 18:55:29,368 -     INFO - 作業ディレクトリにPlaylist作成を開始します.
2022-09-29 18:55:29,414 -     INFO - work/playlists/task_03.json Playlistを出力しました. 曲数:3
2022-09-29 18:55:29,428 -     INFO - work/playlists/task_04.json Playlistを出力しました. 曲数:4
2022-09-29 18:55:29,443 -     INFO - work/playlists/task_05.json Playlistを出力しました. 曲数:16
2022-09-29 18:55:29,458 -     INFO - work/playlists/task_06.json Playlistを出力しました. 曲数:9
2022-09-29 18:55:29,478 -     INFO - work/playlists/task_07.json Playlistを出力しました. 曲数:64
2022-09-29 18:55:29,508 -     INFO - work/playlists/task_08.json Playlistを出力しました. 曲数:165
2022-09-29 18:55:29,543 -     INFO - work/playlists/task_09.json Playlistを出力しました. 曲数:214
2022-09-29 18:55:29,575 -     INFO - work/playlists/task_10.json Playlistを出力しました. 曲数:202
2022-09-29 18:55:29,601 -     INFO - work/playlists/task_11.json Playlistを出力しました. 曲数:126
2022-09-29 18:55:29,616 -     INFO - work/playlists/task_12.json Playlistを出力しました. 曲数:8
2022-09-29 18:55:29,616 -     INFO - 作業ディレクトリにPlaylist作成を完了しました.
2022-09-29 18:55:29,617 -     INFO - PlaylistsディレクトリにPlaylistを配置します。
2022-09-29 18:55:29,658 -     INFO - 10 件のplaylistの配置が完了しました。:C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Playlists
2022-09-29 18:55:29,658 -     INFO - 作業が完了しました.
2022-09-29 18:55:29,659 -     INFO - ---------------------------------
```

### 捕捉 

batをランチャー等に登録しておき、ランチャーから都度呼び出すと便利というのが今のところの個人的な所感です。

## ライセンス

このソフトウェアは、[MITライセンス](https://github.com/hatopopvr/MyBSList/blob/main/LICENSE)のもとで公開されています。

## 連絡先
Twitter [@hatopop_vr](https://twitter.com/hatopop_vr)
