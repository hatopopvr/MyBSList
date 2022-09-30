# MyBSList

ScoreSaberから取得した内容と、星別のフィルタ条件に基づいて星別のプレイリストを作成するスクリプトです.

![img](https://github.com/hatopopvr/MyBSList/blob/main/images/img_explain_001.jpg)

## 背景
星毎に次のようなAccuracy以下の譜面のプレイリストを作成し、クリア埋めと散布図を綺麗するのを加速させる動機で作成しました。
例)★0:98、★1:96、★2:95、★3:93、★4:92、★5:91、★6:88、★7:85、★8:80以下のAccuracyの譜面をそれぞれ抽出

![img](https://github.com/hatopopvr/MyBSList/blob/main/images/img_explain_001.jpg)

## 適用範囲
本プログラムは以下の環境でのみ動作を確認しています。
- Windows 10 pro 64bit

## 使い方

### 導入

[release](https://github.com/hatopopvr/MyBSList/releases)から最新のzipをダウンロードし、任意の場所で解凍します.

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

星毎に作成したいプレイリストの内容に応じて以下の条件を設定してください。

```config.ini
[star00]
# この星のplaylistを作成するか
playlist_is_enable = True
# playしていない譜面をリストに含めるか
not_play_is_enable = True
# NoFailの譜面をリストに含めるか
nf_is_enable = True
# FullComboしていないクリア譜面をリストに含めるか
not_fc_is_enable = False
# クリア譜面について以下フィルタ条件に合致するものをリストに含めるか
filtered_is_enable = True
# クリア譜面についてのフィルタ条件:ppの下限値
filtered_pp_min = 0
# クリア譜面についてのフィルタ条件:ppの上限値
filtered_pp_max = 1000
# クリア譜面についてのフィルタ条件:Accuracyの下限値
filtered_acc_min = 0
# クリア譜面についてのフィルタ条件:Accuracyの上限値
filtered_acc_max = 99
# クリア譜面についてのフィルタ条件:Bad+Missの合計の下限値
filtered_miss_min = 0
# クリア譜面についてのフィルタ条件:Bad+Missの合計の上限値
filtered_miss_max = 10000
# クリア譜面についてのフィルタ条件:順位の下限値
filtered_rank_min = 1000
# クリア譜面についてのフィルタ条件:順位の上限値
filtered_rank_max = 999999
```

### 実行

`MyBSList.exe`をダブルクリックで実行してください。
実行すると、consoleに以下のような内容が出力されておれば、正常に完了しているはずです。
BeatSaberゲーム画面内にて`Refresh Playlist`を実行し、星毎のプレイリストが作成されているか確認してください。

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

`MyBSList.exe`をランチャー等に登録しておき、ランチャーから都度呼び出すと便利というのが今のところの個人的な所感です。


## ライセンス

このソフトウェアは、[MITライセンス](https://github.com/hatopopvr/MyBSList/blob/main/LICENSE)のもとで公開されています。
また、配布するバイナリで使用している各ライセンスにつきましては、

## 連絡先
Twitter [@hatopop_vr](https://twitter.com/hatopop_vr)
