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

### 捕捉 

batをランチャー等に登録しておき、ランチャーから都度呼び出すと便利というのが今のところの個人的な所感です。

## ライセンス

策定中
~~このソフトウェアは、[MITライセンス](https://github.com/hatopopvr/MyBSList/blob/main/LICENSE)のもとで公開されています。~~

## 連絡先
Twitter [@hatopop_vr](https://twitter.com/hatopop_vr)
