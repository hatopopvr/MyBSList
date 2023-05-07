# MyBSList

[ENGLISH](README.md)

ScoreSaberから取得した内容と、条件に基づいて星別のプレイリストを作成するツールです.

![img](https://github.com/hatopopvr/MyBSList/blob/main/images/img_explain_001.jpg)

星毎に次のようなAccuracy以下の範囲の譜面のプレイリストが作成したく、本ツールはそれを支援する目的で作成しました。例）★0:98、★1:96、★2:95、★3:93、★4:92、★5:91、★6:88、★7:85、★8:80以下のAccuracyの譜面を課題譜面としてそれぞれ抽出

![img](https://github.com/hatopopvr/MyBSList/blob/main/images/img_explain_002.jpg)

本ツールの課題譜面抽出は以下の赤の範囲が対象です。

![img](https://github.com/hatopopvr/MyBSList/blob/main/images/img_explain_003.jpg)

## 動作
本プログラムは以下の環境でのみ動作を確認しています。
- Windows 10 pro 64bit

## 導入

[release](https://github.com/hatopopvr/MyBSList/releases)から最新のzipをダウンロードし、任意の場所で解凍します.

## アップデート

`MyBSList`ディレクトリを上書きしてください。動作しない場合は、workディレクトリとlogディレクトリを削除したのち`MyBSList.exe`を実行するようにしてください。

## 使い方

### 設定

`config.ini`を開き、以下を自分の環境に合わせて設定ください。  
Playlistsディレクトリは `[Beat Saberインストールディレクトリ]\Playlists` にあります。

```ini
[user]
# ScoreSaberのPlayerID。変更必須。
player_id = 76561198412839195

# BeatSaberプレイリストのフォルダ
playlist_dir = C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Playlists

[system]
# Playlist Configのファイルパス
playlist_config_path = playlist_config.json
```

星毎に作成したいプレイリストの内容に応じて以下の条件を設定してください。

`playlist_config.json`を作成し、作成したいプレイリストの条件に合わせて以下を設定ください。
`hatopop_playlist_config.json`には私が使っている設定が含まれています。
それを参考にして自分の設定を編集してください。
以下の ※ がついている部分でフィルタリングに必要ない部分は削除しても動作に問題ありません。(v0.2.0で対応しました。)

```json
    {
        "list_name": "star00",                      # Playlistの名称、全て異なる名称にしてください
        "image_path": "images/img_star_00.png",     # Playlistアイコン画像のパス
        "playlist_is_enable": "True",               # この条件のPlaylistを作成するか | True : 作成する
        # flag
        "not_play_is_enable": "True",               # 未プレイ(not play)の譜面をPlaylistに含むか | True : 含む
        "nf_is_enable": "True",                     # NoFailでクリアした譜面をPlaylistに含むか | True : 含む
        "not_fc_is_enable": "False",                # フルコンボ済みの譜面をPlaylistから除外するか | True : 除外する
        "scorefilter_is_enable": "True",            # 以下のスコアフィルタ条件に合致するクリア済み譜面をplaylistに含むか | True : 含む
        # ランク譜面からの曲抽出条件 ※
        "star_min": 0,                              # ★下限 ※               
        "star_max": 1,                              # ★上限 ※
        "nps_min": 0,                               # NPS下限(NPS:秒あたりノーツ数) ※
        "nps_max": 20,                              # NPS上限(NPS:秒あたりノーツ数) ※
        "njs_min": 0,                               # NJS下限(NJS:Notes Jump Speed) ※
        "njs_max": 30,                              # NJS上限(NJS:Notes Jump Speed) ※
        "duration_min": 0,                          # 曲長さ下限(単位: 秒) ※
        "duration_max": 1000,                       # 曲長さ上限(単位: 秒) ※
        "notes_min": 0,                             # Notes数下限 ※
        "notes_max": 10000,                         # Notes数上限 ※
        "bombs_min": 0,                             # ボム数下限 ※
        "bombs_max": 10000,                         # ボム数上限 ※
        "obstacles_min": 0,                         # 壁数下限 ※
        "obstacles_max": 10000,                     # 壁数上限 ※
        # クリア済み譜面のスコアフィルタ ※
        "scorefilter_pp_min": 0,                    # PP下限 ※
        "scorefilter_pp_max": 1000,                 # PP上限 ※
        "scorefilter_acc_min": 0,                   # Accuracy下限(Accが低い譜面を抽出するなど) ※
        "scorefilter_acc_max": 98,                  # Accuracy上限 ※
        "scorefilter_miss_min": 0,                  # Miss(BadCutとMissCutの合計)数の下限 ※
        "scorefilter_miss_max": 10000,              # Miss(BadCutとMissCutの合計)数の上限 ※
        "scorefilter_rank_min": 0,                  # Global Rankの下限 ※
        "scorefilter_rank_max": 999999,             # Global Rankの上限(順位が低い譜面を抽出するなど) ※
        "scorefilter_days_min": 0,                  # スコア更新経過日数下限(更新が古い譜面を抽出するなど) ※
        "scorefilter_days_max": 10000               # スコア更新経過日数上限 ※
    },
```

### 実行

`MyBSList.exe`をダブルクリックで実行してください。
実行すると、consoleに以下のような内容が出力されておれば、正常に完了しているはずです。
BeatSaberゲーム画面内にて`Refresh Playlist`を実行し、プレイリストが作成されているか確認してください。

```
2022-09-29 22:22:42,230 -     INFO - -----------------[start]------------------
2022-09-29 22:22:42,230 -     INFO - Creating working directory.
2022-09-29 22:22:42,230 -     INFO - Work directory creation complete. path:work
2022-09-29 22:22:42,231 -     INFO - Getting player information.
2022-09-29 22:22:42,721 -     INFO - Retrieving player info. hatopop, TotalPlayCount:3,064, RankedPlayCount:2,830, Pages:32
2022-09-29 22:22:42,721 -     INFO - Getting ranked map data.
2022-09-29 22:22:44,951 -     INFO - Retrieving ranked map data completed. path:work\outcome.csv, count:3420
2022-09-29 22:22:44,951 -     INFO - collating ranked map count from LeaderBoard.
2022-09-29 22:22:45,379 -     INFO - ranked map count is 3,420.
2022-09-29 22:22:45,382 -     INFO - Ranked map counts matched. Completing re-acquisition process.
2022-09-29 22:22:45,382 -     INFO - Retrieving Player Score information from ScoreSaber.
2022-09-29 22:22:47,389 -     INFO - Retrieving Player Score information completed. RankedPlayCount is 2,830.
2022-09-29 22:22:47,390 -     INFO - Start recalculating Acc based on number of notes and combos.
2022-09-29 22:22:47,399 -     INFO - There are 42 results where the Acc is different from the game.
2022-09-29 22:22:47,400 -     INFO - Acc recalculated results overwritten.
2022-09-29 22:22:47,400 -     INFO - creating combined data.
2022-09-29 22:22:47,451 -     INFO - Merge complete. Count:3,420
2022-09-29 22:22:47,455 -     INFO - delete playlist in working directory.
2022-09-29 22:22:47,457 -     INFO - Playlist deletion in working directory complete. count:10
2022-09-29 22:22:47,457 -     INFO - <<Playlist creation in working directory start.>>
2022-09-29 22:22:47,499 -     INFO - Playlist: work/playlists/task_03.json, Count:3
2022-09-29 22:22:47,521 -     INFO - Playlist: work/playlists/task_04.json, Count:4
2022-09-29 22:22:47,537 -     INFO - Playlist: work/playlists/task_05.json, Count:16
2022-09-29 22:22:47,552 -     INFO - Playlist: work/playlists/task_06.json, Count:9
2022-09-29 22:22:47,571 -     INFO - Playlist: work/playlists/task_07.json, Count:64
2022-09-29 22:22:47,598 -     INFO - Playlist: work/playlists/task_08.json, Count:165
2022-09-29 22:22:47,629 -     INFO - Playlist: work/playlists/task_09.json, Count:214
2022-09-29 22:22:47,659 -     INFO - Playlist: work/playlists/task_10.json, Count:202
2022-09-29 22:22:47,683 -     INFO - Playlist: work/playlists/task_11.json, Count:126
2022-09-29 22:22:47,697 -     INFO - Playlist: work/playlists/task_12.json, Count:8
2022-09-29 22:22:47,698 -     INFO - <<Playlist creation in working directory complete.>>
2022-09-29 22:22:47,698 -     INFO - Copy and paste the playlists into the playlists directory.
2022-09-29 22:22:47,734 -     INFO - 10 playlists have been completed.:C:\Program Files (x86)\Steam\steamapps\common\Beat Saber\Playlists
2022-09-29 22:22:47,735 -     INFO - ----------------[complete]-----------------
```

### 補足

- `MyBSList.exe`をランチャー等に登録しておき、ランチャーから都度呼び出すと便利というのが今のところの個人的な所感です。
- 使いながら利便性の良い仕様を模索している状態のため、仕様は暫定的であり今後大きく変わる可能性があります。

## データ

- Score情報 - [ScoreSaber](https://scoresaber.com/) Public API - [doc](https://docs.scoresaber.com/)  
- Rank譜面データ - らっきょさん([rakkyo150](https://twitter.com/rakkyo150)) の [RankedMapData](https://github.com/rakkyo150/RankedMapData)

## ライセンス

このソフトウェアは、[MITライセンス](https://github.com/hatopopvr/MyBSList/blob/main/LICENSE)のもとで公開されています。  
また、配布するバイナリで使用している各ライセンスにつきましては、[exe_used_license](https://github.com/hatopopvr/MyBSList/blob/main/exe_used_license)を参照願います。

## 連絡先
Twitter [@hatopop_vr](https://twitter.com/hatopop_vr)
