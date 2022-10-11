#import libs.playlist_downloader as pl
from distutils.util import strtobool
import configparser
import base64
import math
import json
import urllib3
from tqdm import tqdm
from datetime import datetime
import json
from pandas import json_normalize
import pandas as pd
import shutil
import os
import warnings
from logging import getLogger, INFO, DEBUG, StreamHandler, FileHandler, Formatter
warnings.filterwarnings("ignore")
#from dateutil import tz

# ---------------------------------------
# 列情報の設定
# ---------------------------------------
# Score csv保存用列
cols_score = ["Song", "Level", "Stars", "Acc", "FC", "Rank", "PP", "Miss", "Bad", "Combo", "Score", "Difficulty", "Play", "DailyPlay",
              "Bpm", "Duration", "Notes", 'Nps', "Njs", "Bombs", "Obstacles", 'Upvotesratio', "Upvotes", "Downvotes", "Ranked", "Days",
              "Tags"]

# Playlist用列
cols_playlist = ['Hash', 'SongName', 'SongAuthor', 'LevelAuthor', 'Difficulty', 'Notes', 'Duration',
                 'Characteristic', 'Level', 'Stars', 'Maxscore', 'Acc', 'Score', 'Bad', 'Miss', 'Nps',
                 'PP', 'Rank', 'Modifiers', 'DateUtc', 'Date', 'Days', 'FC']


class MyBSList:
    def __init__(self, config):
        """_コンストラクタです_

        Args:
            config (_type_): _path関係など主要なconfigです_
        """
        self.config = config

        # user ------------------------------
        # BeatSaber Playlistsのディレクトリ
        self.playlist_dir = config['user']['playlist_dir']
        # ScoreSaberのPlayerID
        self.player_id = config['user']['player_id']

        # system-----------------------------
        # rankedmapdata_url: ランク譜面データのcsvのURLです.らっきょさんデータ.
        self.rankedmapdata_url = config['system']['url']
        # 作業ディレクトリ
        self.work_dir = os.path.join(
            config['system']['work_dir'], datetime.now().strftime('%Y%m%d%H%M%S'))
        # logdir
        self.log_dir = config['system']['log_dir']
        # 差分ダウンロード有効フラグ
        self.saved_player_score_is_enable = strtobool(
            config['system']['saved_player_score_is_enable'])
        # MaxScore,Accを再計算した値をMaxScore,Accに上書きするか。
        self.acc_recalq_override_is_enable = strtobool(
            config['system']['acc_recalq_override_is_enable'])

        self.page_count = int(config['system']['page_count'])

        self.data_path = config['system']['work_dir']

        # カスタムタスクjsonのパス
        self.playlist_config_path = config['system']['playlist_config_path']

        # player情報の親フォルダ(data_pathの子フォルダ)
        self.player_path = r"{}/players_data/{}".format(
            self.data_path, self.player_id)

        # playerinfoの保存先
        self.player_info_path = r"{}/player_info_{}.csv".format(
            self.player_path, self.player_id)
        # playerのscore関連保存先
        self.player_score_path = r"{}/scores_full_{}.csv".format(
            self.player_path, self.player_id)
        self.player_ranked_path = r"{}/scores_ranked_{}.csv".format(
            self.player_path, self.player_id)
        self.player_score_pickle_path = r"{}/scores_ranked_{}.pkl".format(
            self.player_path, self.player_id)

        # 曲情報の保存先
        self.song_list_path = r"{}/song_list_full.csv".format(self.data_path)
        self.song_ranked_path = r"{}/song_ranked.csv".format(self.data_path)

        # levelclearランク除外関連パス
        self.level_cleared_path = r"{}/level_cleared_{}.csv".format(
            self.player_path, self.player_id)

        # playlistの保存
        self.playlist_path = r"{}/playlists".format(self.data_path)

        # タイムゾーンの設定
        self.tz_ja = pd.Timestamp(datetime.now()).tz_localize(
            'UTC').tz_convert('Asia/Tokyo')

    def set_logger(self):
        """ logger を作成します。
        """
        # loggerの取得
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(self.log_dir, 'log_{}.log'.format(
            datetime.now().strftime('%Y%m%d')))

        self.logger = getLogger(__name__)
        self.logger.setLevel(INFO)

        handler1 = StreamHandler()
        handler1.setFormatter(
            Formatter("%(asctime)s - %(levelname)8s - %(message)s"))

        # handler2を作成
        handler2 = FileHandler(filename=log_file)  # handler2はファイル出力
        # handler2.setLevel(INFO)     #handler2はLevel.WARN以上
        handler2.setFormatter(
            Formatter("%(asctime)s - %(levelname)8s - %(message)s"))

        # loggerに2つのハンドラを設定
        self.logger.addHandler(handler1)
        self.logger.addHandler(handler2)

    def process(self):
        """ 一連の処理を実行します.
        """
        self.set_logger()
        self.logger.info("-----------------[start]------------------")
        try:
            self.create()
            _, self.RangeCount = self.get_player_info()
            df_rankmap_data = self.get_ranked_song_data()
            df_rankmap_data = self.get_ranked_song_data_from_leaderboard(
                df_rankmap_data)
            df_scores = self.get_player_score_data(
                self.RangeCount, df_rankmap_data)
            df_scores = self.recalq_accuracy(df_scores)
            df_rankmap_data_append = self.merge_scores_ranked(
                df_rankmap_data, df_scores)
            self.clean_playlist_json(self.playlist_path, self.playlist_dir)
            self.create_playlist_json(df_rankmap_data_append, self.config)
            self.copy_to_playlist(self.playlist_path, self.playlist_dir)
        except:
            self.logger.error("Error is occur.", exc_info=True)
        self.logger.info("----------------[complete]-----------------")

    def create(self):
        """_作業ディレクトリを作成します_
        """
        self.logger.info("Creating working directory.")

        # データ大元のフォルダ作成
        if os.path.exists(self.data_path) == False:
            self.logger.debug(
                'MyBeatSaberAnalytics用のデータ格納フォルダをGoogle Driveに新規作成します.')
            self.logger.debug('データ格納フォルダ:{}'.format(self.data_path))
            os.makedirs(self.data_path, exist_ok=True)
            self.logger.debug('作成が完了しました.')

        # データ大元のフォルダ作成
        if os.path.exists(self.player_path) == False:
            self.logger.debug(
                'PlayerID:{}用のデータ格納フォルダを新規作成します.'.format(self.player_id))
            self.logger.debug('playerフォルダ:{}'.format(self.player_path))
            self.logger.debug('作成が完了しました.')
            os.makedirs(self.player_path, exist_ok=True)

        # プレイヤー用のフォルダ作成
        if os.path.exists(self.playlist_path) == False:
            self.logger.debug('Playlist格納用のフォルダを新規作成します.')
            self.logger.debug('Playlist格納フォルダ:{}'.format(self.playlist_path))
            os.makedirs(self.playlist_path, exist_ok=True)
            self.logger.debug('作成が完了しました.')
        self.logger.info(
            "Work directory creation complete. path:{}".format(self.data_path))
        return

    def get_player_info(self):
        """_プレイヤー情報を取得します_

        Returns:
            _df_info : DataFrame
                プレイヤー情報のDataFrameです.
            RangeCount : int
                ScoreSaberのPage数です.
        """

        self.logger.info('Getting player information.')
        url = r"https://scoresaber.com/api/player/{}/full".format(
            self.player_id)

        http = urllib3.PoolManager()
        r = http.request('GET', url)
        res_data = json.loads(r.data.decode('utf-8'))
        _df_info = json_normalize(res_data)

        _df_info["TotalScore"] = _df_info["scoreStats.totalScore"]
        _df_info["RankedScore"] = _df_info["scoreStats.totalRankedScore"]
        _df_info["AveRankedAcc"] = _df_info["scoreStats.averageRankedAccuracy"]
        _df_info["TotalPlay"] = _df_info["scoreStats.totalPlayCount"]
        _df_info["RankedPlay"] = _df_info["scoreStats.rankedPlayCount"]
        _df_info["ReplayWatched"] = _df_info["scoreStats.replaysWatched"]
        _df_info["ScoreDate"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        _df_info["ScoreDateUtc"] = pd.to_datetime(
            _df_info['ScoreDate'], utc=True)
        _df_info_idx = _df_info.set_index("ScoreDateUtc")
        _df_info["ScoreDateJa"] = _df_info_idx.index.tz_convert("Asia/Tokyo")

        TotalPlay = _df_info["TotalPlay"][0]
        RankedPlay = _df_info["RankedPlay"][0]
        RangeCount = math.ceil(TotalPlay / self.page_count) + 1
        self.logger.info("Retrieving player info. {}, TotalPlayCount:{:,}, RankedPlayCount:{:,}, Pages:{:,}".format(
            _df_info["name"][0], TotalPlay, RankedPlay, RangeCount))
        return _df_info, RangeCount

    def get_ranked_song_data(self):
        """_ランク譜面の曲情報データフレームを取得します._

        Returns:
            df_rankmap_data : DataFrame
        """
        self.logger.info('Getting ranked map data.')
        headers = {
            'Accept': 'application/vnd.github.v3+json',
        }

        http = urllib3.PoolManager()
        r = http.request('GET', self.rankedmapdata_url, headers=headers)
        data = json.loads(r.data.decode('utf-8'))

        # 最新releaseのcsvのurl取得
        url_rankmap_data = data[0]["assets"][0]["browser_download_url"]

        file_name = os.path.join(
            self.data_path, os.path.basename(url_rankmap_data))

        result = http.request('GET', url_rankmap_data, preload_content=False)

        with open(file_name, 'wb') as out_file:
            shutil.copyfileobj(result, out_file)

        result.release_conn()

        df_rankmap_data = pd.read_csv(file_name)
        df_rankmap_data = df_rankmap_data[[
            x for x in df_rankmap_data.columns if not x.startswith("Unnamed")]]
        df_rankmap_data["hash"] = df_rankmap_data["hash"].str.upper()

        df_rankmap_data = df_rankmap_data.rename(
            columns=lambda x: x.capitalize())

        df_rankmap_data.rename(columns={
            "Songname": "SongName",
            "Songsubname": "SongSub",
            "Songauthorname": "SongAuthor",
            "Levelauthorname": "LevelAuthor"
        }, inplace=True)

        # 準備
        df_rankmap_data["Song"] = df_rankmap_data["SongName"] + " / " + \
            df_rankmap_data["SongAuthor"] + \
            " [" + df_rankmap_data["LevelAuthor"] + "]"
        df_rankmap_data["Level"] = df_rankmap_data["Stars"].astype("int")
        df_rankmap_data["LevelStr"] = df_rankmap_data["Level"].astype("str")
        self.logger.info('Retrieving ranked map data completed. path:{}, count:{:,}'.format(
            file_name, len(df_rankmap_data["Hash"])))
        return df_rankmap_data

    def get_ranked_song_data_from_leaderboard(self, _df_rankmap_data):
        """_ScoreSaber LeaderBoardからランク譜面データフレームを再取得します._
            この処理は全譜面数が一致しない場合に限ります.

        Args:
            _df_rankmap_data (DataFrame): ランク譜面データフレーム

        Returns:
            _df_rankmap_data : DataFrame ランク譜面データフレーム
        """
        self.logger.info('Collating ranked map count from LeaderBoard.')

        url = r"https://scoresaber.com/api/leaderboards?ranked=true&page=1&withMetadata=true"

        http = urllib3.PoolManager()
        response = http.request('GET', url)
        res_data = json.loads(response.data.decode('utf-8'))
        total_count_from_leaderboard = res_data['metadata']['total']
        level_count_page = res_data['metadata']['itemsPerPage']

        scoresaber_ranked_page_count = math.ceil(
            total_count_from_leaderboard / level_count_page)
        self.logger.info("Ranked map count is {:,}.".format(
            total_count_from_leaderboard))  # , scoresaber_ranked_page_count))
        df_ranked_songs_from_leaderboard = json_normalize(
            res_data['leaderboards'])

        if len(_df_rankmap_data["Hash"]) != total_count_from_leaderboard:
            self.logger.info(
                'Ranked map count do not match. Start re-acquisition.')
            for i in tqdm(range(2, scoresaber_ranked_page_count+1)):
                url = r"https://scoresaber.com/api/leaderboards?ranked=true&page={}".format(
                    i)
                try:
                    http = urllib3.PoolManager()
                    response = http.request('GET', url)
                    res_data = json.loads(response.data.decode('utf-8'))
                    df_ranked_songs_from_leaderboard = df_ranked_songs_from_leaderboard.append(
                        json_normalize(res_data['leaderboards']), ignore_index=True)
                except:
                    break

            def func_mode(x):
                if x == "SoloStandard":
                    return "Standard"
                else:
                    return x

            df_ranked_songs_from_leaderboard['Hash'] = df_ranked_songs_from_leaderboard['songHash'].str.upper(
            )
            df_ranked_songs_from_leaderboard['Song'] = df_ranked_songs_from_leaderboard['songName'] + " " + df_ranked_songs_from_leaderboard['songSubName'] + \
                " / " + df_ranked_songs_from_leaderboard['songAuthorName'] + \
                " [" + df_ranked_songs_from_leaderboard['levelAuthorName'] + "]"
            df_ranked_songs_from_leaderboard['SongName'] = df_ranked_songs_from_leaderboard['songName']
            df_ranked_songs_from_leaderboard['SongSub'] = df_ranked_songs_from_leaderboard['songSubName']
            df_ranked_songs_from_leaderboard['SongAuthor'] = df_ranked_songs_from_leaderboard['songAuthorName']
            df_ranked_songs_from_leaderboard['LevelAuthor'] = df_ranked_songs_from_leaderboard['levelAuthorName']
            df_ranked_songs_from_leaderboard['Mode'] = df_ranked_songs_from_leaderboard['difficulty.gameMode'].apply(
                func_mode)
            _df_ranked_songs_from_leaderboard = df_ranked_songs_from_leaderboard['difficulty.difficultyRaw'].str.split(
                '_', expand=True)
            _df_ranked_songs_from_leaderboard.columns = [
                '_', 'Difficulty', 'Mode']
            df_ranked_songs_from_leaderboard['Difficulty'] = _df_ranked_songs_from_leaderboard['Difficulty']
            df_ranked_songs_from_leaderboard['Stars'] = df_ranked_songs_from_leaderboard['stars']
            df_ranked_songs_from_leaderboard['Level'] = df_ranked_songs_from_leaderboard['Stars'].astype(
                'int')
            df_ranked_songs_from_leaderboard["LevelStr"] = df_ranked_songs_from_leaderboard['Level'].astype(
                'str')
            self.logger.info("RankedSong(ScoreSaber leaderboard):{:,}".format(
                df_ranked_songs_from_leaderboard["Song"].count()))
            if total_count_from_leaderboard == df_ranked_songs_from_leaderboard["Song"].count():
                ranked_song_from_leaderboard_is_enable = True
            else:
                self.logger.info(
                    'Ranked map counts unmatched. something trouble is occur.')
                return _df_rankmap_data

        else:
            self.logger.info(
                'Ranked map counts matched. Completing re-acquisition process.')
            return _df_rankmap_data

        return df_ranked_songs_from_leaderboard

    def get_player_score_data(self, _RangeCount, _df_rankmap_data):
        """_ScoreSaberからplayerのScore情報を取得します._

        Args:
            _RangeCount (_int_): _取得するページ数です._
            _df_rankmap_data (_DataFrame_): _ランク譜面全データのデータフレームです._

        Returns:
            _DataFrame_: _プレイヤーのScore情報のデータフレームです._
        """
        self.logger.info(
            'Retrieving Player Score information from ScoreSaber.')

        if self.saved_player_score_is_enable and os.path.exists(self.player_score_pickle_path):
            df_scores_pkl = pd.read_pickle(self.player_score_pickle_path)
            _df_scores_pkl = df_scores_pkl.head(0)

            i = 1
            while True:
                url = r"https://scoresaber.com/api/player/{}/scores?sort=recent&page={}&limit={}".format(
                    self.player_id, i, self.page_count)
                try:
                    http = urllib3.PoolManager()
                    response = http.request('GET', url)
                    res_data = json.loads(response.data.decode('utf-8'))
                    _df_scores_pkl = _df_scores_pkl.append(
                        json_normalize(res_data['playerScores']), ignore_index=True)
                    if df_scores_pkl['score.timeSet'].max() > _df_scores_pkl['score.timeSet'].min():
                        break
                except:
                    break

            _df_scores = df_scores_pkl.append(_df_scores_pkl, ignore_index=True).sort_values(
                "score.timeSet", ascending=False).groupby("score.id").head(1)

        else:
            url = r"https://scoresaber.com/api/player/{}/scores?sort=recent&limit={}".format(
                self.player_id, self.page_count)
            http = urllib3.PoolManager()
            response = http.request('GET', url)
            res_data = json.loads(response.data.decode('utf-8'))
            _df_scores = json_normalize(res_data['playerScores'])

            for i in tqdm(range(2, _RangeCount)):
                url = r"https://scoresaber.com/api/player/{}/scores?sort=recent&page={}&limit={}".format(
                    self.player_id, i, self.page_count)
                try:
                    http = urllib3.PoolManager()
                    response = http.request('GET', url)
                    res_data = json.loads(response.data.decode('utf-8'))
                    _df_scores = _df_scores.append(json_normalize(
                        res_data['playerScores']), ignore_index=True)
                except:
                    break

        # 未加工データ保存
        _df_scores.to_pickle(self.player_score_pickle_path)

        _df_scores['Song'] = _df_scores['leaderboard.songName'] + " " + _df_scores['leaderboard.songSubName'] + \
            " / " + _df_scores['leaderboard.songAuthorName'] + \
            " [" + _df_scores['leaderboard.levelAuthorName'] + "]"
        _df_scores['SongName'] = _df_scores['leaderboard.songName']
        _df_scores['SongSub'] = _df_scores['leaderboard.songSubName']
        _df_scores['SongAuthor'] = _df_scores['leaderboard.songAuthorName']
        _df_scores['LevelAuthor'] = _df_scores['leaderboard.levelAuthorName']
        _df_scores['Hash'] = _df_scores['leaderboard.songHash'].str.upper()
        _df_scores['Acc'] = _df_scores['score.modifiedScore'] / \
            _df_scores['leaderboard.maxScore'] * 100
        _df_scores['MaxScore'] = _df_scores['leaderboard.maxScore']
        _df_scores['Mode'] = _df_scores['leaderboard.difficulty.gameMode'].apply(
            self.func_mode)
        __df_scores = _df_scores['leaderboard.difficulty.difficultyRaw'].str.split(
            '_', expand=True)
        __df_scores.columns = ['_', 'Difficulty', 'Mode']
        _df_scores['Difficulty'] = __df_scores['Difficulty']
        _df_scores['Stars'] = _df_scores['leaderboard.stars']
        _df_scores['Level'] = _df_scores['Stars'].astype('int')
        _df_scores["LevelStr"] = _df_scores['Level'].astype('str')
        _df_scores['Score'] = _df_scores['score.modifiedScore']
        _df_scores['Bad'] = _df_scores['score.badCuts']
        _df_scores['Miss'] = _df_scores['score.missedNotes']
        _df_scores['Combo'] = _df_scores['score.maxCombo']
        _df_scores['PP'] = _df_scores['score.pp']
        _df_scores['Rank'] = _df_scores['score.rank']
        _df_scores['Modifiers'] = _df_scores['score.modifiers']
        _df_scores['Ranked'] = _df_scores['leaderboard.ranked']
        _df_scores['DateUtc'] = pd.to_datetime(_df_scores['score.timeSet'])
        _df_scores_idx = _df_scores.set_index('DateUtc')
        _df_scores['DateJa'] = _df_scores_idx.index.tz_convert('Asia/Tokyo')
        _df_scores['Date'] = _df_scores['DateJa'].dt.date
        _df_scores['Days'] = (self.tz_ja.date() - _df_scores['Date']).dt.days
        _df_scores = _df_scores.set_index('DateJa')
        _df_scores['FC'] = _df_scores['score.fullCombo'].apply(self.func_fc)

        _df_scores = _df_scores[[
            x for x in _df_scores.columns if not x.startswith("score.")]]
        _df_scores = _df_scores[[
            x for x in _df_scores.columns if not x.startswith("leaderboard.")]]

        # 改行コード等の除去
        for col in _df_scores.columns:
            try:
                if len(_df_scores[_df_scores[col].str.contains("\n")][[col]]) == 0:
                    continue
                else:
                    _df_scores[col] = _df_scores[col].str.replace("\n", "")
            except:
                continue

        for col in _df_scores.columns:
            try:
                if len(_df_scores[_df_scores[col].str.contains("\r")][[col]]) == 0:
                    continue
                else:
                    _df_scores[col] = _df_scores[col].str.replace("\r", "")
            except:
                continue

        # RankedMap(らっきょさんのBeatSaverデータ)の情報結合
        _df_scores = _df_scores.reset_index()
        _df_scores = pd.merge(_df_scores, _df_rankmap_data, on=[
                              "Hash", "Difficulty"], how="left", suffixes=("", "_y"))
        _df_scores = _df_scores[[
            x for x in _df_scores.columns if not x.endswith("_y")]]
        _df_scores = _df_scores.set_index("DateJa")

        # Score情報の保存
        _df_scores[(_df_scores['Ranked'] == True)][cols_score].sort_index(
            ascending=False).to_csv(self.player_ranked_path)
        _df_scores = _df_scores[(_df_scores['Ranked'] == True)].sort_index(
            ascending=False)
        _df_scores.sort_index(ascending=False).to_csv(
            self.player_score_path.format(self.player_id))

        self.logger.info('Retrieving Player Score information completed. RankedPlayCount is {:,}.'.format(
            _df_scores['Play'].count()))
        return _df_scores

    def recalq_accuracy(self, _df_scores):
        """_notes数とcombo数に基づきAccを再計算し、Score情報を上書きします._

        Args:
            _df_scores (_DataFrame_): _Playerのスコア情報のデータフレームです._

        Returns:
            _DataFrame_: _Accを再計算し上書きしたスコア情報のデータフレームです._
        """
        self.logger.info(
            'Start recalculating Acc based on number of notes and combos.')

        def func_max_score(_notes):
            """ notes数とcombo数に基づいた最大スコアの再計算
            """
            combo_a = 115 * 1
            combo_b = 115 * 2
            combo_c = 115 * 4
            combo_d = 115 * 8

            if _notes >= 14:
                return combo_d * (_notes - 13) + combo_a + combo_b * 4 + combo_c * 8
            elif _notes >= 6:
                return combo_c * (_notes - 5) + combo_a + combo_b * 4
            elif _notes >= 2:
                return combo_b * (_notes - 1) + combo_a
            elif _notes >= 1:
                return combo_a
            else:
                return 0

        _df_scores['MaxScore'] = _df_scores['MaxScore']
        _df_scores['MaxScoreRecalq'] = _df_scores['Notes'].apply(
            func_max_score)
        _df_scores['AccRecalq'] = _df_scores['Score'] / \
            _df_scores['MaxScoreRecalq'] * 100
        _df_scores['MaxScoreDiff'] = _df_scores['MaxScore'].fillna(
            0) - _df_scores['MaxScoreRecalq'].fillna(0)
        _df_scores['AccDiff'] = _df_scores['Acc'].fillna(
            0) - _df_scores['AccRecalq'].fillna(0)

        df_errors = _df_scores[
            (1 == 1)
            & (_df_scores['Ranked'])
            & (_df_scores['MaxScoreDiff'] != 0)
        ]

        self.logger.info(
            'There are {} results where the Accuracy is different from the game.'.format(len(df_errors)))

        if self.acc_recalq_override_is_enable:
            _df_scores.rename(columns={
                "MaxScore": "MaxScoreOrg",
                "Acc": "AccOrg",
            }, inplace=True)
            _df_scores.rename(columns={
                "MaxScoreRecalq": "MaxScore",
                "AccRecalq": "Acc",
            }, inplace=True)
            self.logger.info('Accuracy recalculated results overwritten.')
        return _df_scores

    def merge_scores_ranked(self, _df_rankmap_data, _df_scores):
        """_結合データを作成します._

        Args:
            _df_rankmap_data (_DataFrame_): _ランク譜面データ_
            _df_scores (_DataFrame_): _プレイヤのランク譜面のスコアデータ_

        Returns:
            _DataFrame_: _結合データ_
        """
        self.logger.info('Creating merged data.')
        _df_rankmap_data_append = pd.merge(_df_rankmap_data, _df_scores.reset_index(
        ), on=["Hash", "Difficulty"], how="left", suffixes=("", "_y"))[cols_playlist]
        _df_rankmap_data_append = _df_rankmap_data_append[[
            x for x in _df_rankmap_data_append.columns if not x.endswith("_y")]]
        self.logger.info('Merge complete. Count:{:,}'.format(
            len(_df_rankmap_data_append)))
        return _df_rankmap_data_append

    def create_playlist(self, _df_rankmap_data_append, config):
        """ Playlistを作成
        """
        self.logger.info('<<Playlist creation in working directory start.>>')

        def image_file_to_base64(_file_path):
            """ 画像ファイルをBase64エンコードし文字列に変換
            """
            with open(_file_path, "rb") as image_file:
                data = base64.b64encode(image_file.read())

            return "data:image/png;base64,{}".format(data.decode('utf-8'))

        for level_i in range(13):
            star_i = "star{:02d}".format(level_i)
            playlist_is_enable = strtobool(
                config[star_i]['playlist_is_enable'])
            not_play_is_enable = strtobool(
                config[star_i]['not_play_is_enable'])
            nf_is_enable = strtobool(config[star_i]['nf_is_enable'])
            not_fc_is_enable = strtobool(config[star_i]['not_fc_is_enable'])
            filtered_is_enable = strtobool(
                config[star_i]['filtered_is_enable'])
            filtered_pp_min = int(config[star_i]['filtered_pp_min'])
            filtered_pp_max = int(config[star_i]['filtered_pp_max'])
            filtered_acc_min = int(config[star_i]['filtered_acc_min'])
            filtered_acc_max = int(config[star_i]['filtered_acc_max'])
            filtered_miss_min = int(config[star_i]['filtered_miss_min'])
            filtered_miss_max = int(config[star_i]['filtered_miss_max'])
            filtered_rank_min = int(config[star_i]['filtered_rank_min'])
            filtered_rank_max = int(config[star_i]['filtered_rank_max'])

            if not playlist_is_enable:
                continue

            df_playlist = _df_rankmap_data_append.head(0)
            _df_not_cleaed_playlist = _df_rankmap_data_append.head(0)
            _df_filtered_playlist = _df_rankmap_data_append  # .head(0)

            # not played
            if not_play_is_enable:
                _df_not_cleaed_playlist = _df_not_cleaed_playlist.append(_df_rankmap_data_append[(1 == 1)
                                                                                                 & (_df_rankmap_data_append["Level"] == level_i)
                                                                                                 & (_df_rankmap_data_append['Score'].isnull())
                                                                                                 ])

            # NF
            if nf_is_enable:
                _df_not_cleaed_playlist = _df_not_cleaed_playlist.append(_df_rankmap_data_append[(1 == 1)
                                                                                                 & (_df_rankmap_data_append["Level"] == level_i)
                                                                                                 & (_df_rankmap_data_append['Modifiers'] == 'NF')
                                                                                                 ])

            if filtered_is_enable or not_fc_is_enable:
                _df_filtered_playlist = _df_rankmap_data_append
            else:
                _df_filtered_playlist = _df_rankmap_data_append.head(0)

            # Filtered
            if filtered_is_enable:
                _df_filtered_playlist = _df_filtered_playlist[(1 == 1)
                                                              & (_df_rankmap_data_append["Level"] == level_i)
                                                              & (_df_rankmap_data_append["PP"] >= filtered_pp_min)
                                                              & (_df_rankmap_data_append["PP"] <= filtered_pp_max)
                                                              & (_df_rankmap_data_append["Acc"] >= filtered_acc_min)
                                                              & (_df_rankmap_data_append["Acc"] <= filtered_acc_max)
                                                              & (_df_rankmap_data_append["Rank"] >= filtered_rank_min)
                                                              & (_df_rankmap_data_append["Rank"] <= filtered_rank_max)
                                                              & (_df_rankmap_data_append["Miss"] + _df_rankmap_data_append["Bad"] >= filtered_miss_min)
                                                              & (_df_rankmap_data_append["Miss"] + _df_rankmap_data_append["Bad"] <= filtered_miss_max)
                                                              & (_df_rankmap_data_append['Modifiers'] != 'NF')
                                                              ]

            # Not FC
            if not_fc_is_enable:
                _df_filtered_playlist = _df_filtered_playlist[(1 == 1)
                                                              & (_df_rankmap_data_append["Level"] == level_i)
                                                              & (_df_rankmap_data_append['FC'] == '-')
                                                              ]

            df_playlist = df_playlist.append(_df_not_cleaed_playlist)
            df_playlist = df_playlist.append(_df_filtered_playlist)

            # playlist化
            if len(df_playlist) > 0:
                songs = []
                for i, x in df_playlist.iterrows():
                    songs += [{
                        "songName": x["SongName"],
                        "levelAuthorName": x["LevelAuthor"],
                        "hash": x["Hash"],
                        "levelid": f"custom_level_{x['Hash']}",
                        "difficulties": [
                            {
                                "characteristic": "Standard",
                                "name": x["Difficulty"]
                            }
                        ]
                    }]

                _img_url = r"images/img_star_{:02d}.png".format(level_i)

                playlist = {
                    "playlistTitle": "task_{:02d}_{}".format(level_i, self.tz_ja.strftime("%m%d")),
                    "playlistAuthor": "hatopop",
                    "songs": songs, "image": image_file_to_base64(_img_url)
                }

                song_playlist_path = r"{}/task_{:02d}.json".format(
                    self.playlist_path, level_i, datetime.now().strftime("%Y%m%d"))

                with open(song_playlist_path, "w") as f:
                    json.dump(playlist, f)

                self.logger.info("Playlist: {}, Count:{}".format(
                    song_playlist_path, len(df_playlist)))
        self.logger.info(
            "<<Playlist creation in working directory complete.>>")
        return

    def create_playlist_json(self, _df_rankmap_data_append, _config):
        """ jsonのsettinファイルを用いてPlaylistを作成
        """
        self.logger.info('<<Playlist creation in working directory start.>>')

        def image_file_to_base64(_file_path):
            """ 画像ファイルをBase64エンコードし文字列に変換
            """
            with open(_file_path, "rb") as image_file:
                data = base64.b64encode(image_file.read())

            return "data:image/png;base64,{}".format(data.decode('utf-8'))

        json_open = open(self.playlist_config_path, 'r')
        list_configs = json.load(json_open)

        for config in list_configs:
            playlist_is_enable = strtobool(
                config['playlist_is_enable'])
            not_play_is_enable = strtobool(
                config['not_play_is_enable'])
            nf_is_enable = strtobool(config['nf_is_enable'])
            not_fc_is_enable = strtobool(config['not_fc_is_enable'])
            scorefilter_is_enable = strtobool(
                config['scorefilter_is_enable'])
            star_min = (config['star_min'])
            star_max = (config['star_max'])
            nps_min = (config['nps_min'])
            nps_max = (config['nps_max'])
            duration_min = (config['duration_min'])
            duration_max = (config['duration_max'])
            scorefilter_pp_min = (config['scorefilter_pp_min'])
            scorefilter_pp_max = (config['scorefilter_pp_max'])
            scorefilter_acc_min = (config['scorefilter_acc_min'])
            scorefilter_acc_max = (config['scorefilter_acc_max'])
            scorefilter_miss_min = (config['scorefilter_miss_min'])
            scorefilter_miss_max = (config['scorefilter_miss_max'])
            scorefilter_rank_min = (config['scorefilter_rank_min'])
            scorefilter_rank_max = (config['scorefilter_rank_max'])

            if not playlist_is_enable:
                continue

            df_playlist = _df_rankmap_data_append.head(0)
            _df_not_cleared_playlist = _df_rankmap_data_append.head(0)
            _df_filtered_playlist = _df_rankmap_data_append

            # not played
            if not_play_is_enable:
                _df_not_cleared_playlist = _df_not_cleared_playlist.append(_df_rankmap_data_append[(1 == 1)
                                                                                                   & (_df_rankmap_data_append["Stars"] >= star_min)
                                                                                                   & (_df_rankmap_data_append["Stars"] < star_max)
                                                                                                   & (_df_rankmap_data_append["Nps"] >= nps_min)
                                                                                                   & (_df_rankmap_data_append["Nps"] < nps_max)
                                                                                                   & (_df_rankmap_data_append["Duration"] >= duration_min)
                                                                                                   & (_df_rankmap_data_append["Duration"] < duration_max)
                                                                                                   & (_df_rankmap_data_append['Score'].isnull())
                                                                                                   ])

            # NF
            if nf_is_enable:
                _df_not_cleared_playlist = _df_not_cleared_playlist.append(_df_rankmap_data_append[(1 == 1)
                                                                                                   & (_df_rankmap_data_append["Stars"] >= star_min)
                                                                                                   & (_df_rankmap_data_append["Stars"] < star_max)
                                                                                                   & (_df_rankmap_data_append["Nps"] >= nps_min)
                                                                                                   & (_df_rankmap_data_append["Nps"] < nps_max)
                                                                                                   & (_df_rankmap_data_append["Duration"] >= duration_min)
                                                                                                   & (_df_rankmap_data_append["Duration"] < duration_max)
                                                                                                   & (_df_rankmap_data_append['Modifiers'] == 'NF')
                                                                                                   ])

            if scorefilter_is_enable or not_fc_is_enable:
                _df_filtered_playlist = _df_rankmap_data_append
            else:
                _df_filtered_playlist = _df_rankmap_data_append.head(0)

            # SongFiltered
            _df_filtered_playlist = _df_filtered_playlist[(1 == 1)
                                                          & (_df_rankmap_data_append["Stars"] >= star_min)
                                                          & (_df_rankmap_data_append["Stars"] < star_max)
                                                          & (_df_rankmap_data_append["Nps"] >= nps_min)
                                                          & (_df_rankmap_data_append["Nps"] < nps_max)
                                                          & (_df_rankmap_data_append["Duration"] >= duration_min)
                                                          & (_df_rankmap_data_append["Duration"] < duration_max)
                                                          ]

            # ScoreFiltered
            if scorefilter_is_enable:
                _df_filtered_playlist = _df_filtered_playlist[(1 == 1)
                                                              & (_df_rankmap_data_append["PP"] >= scorefilter_pp_min)
                                                              & (_df_rankmap_data_append["PP"] < scorefilter_pp_max)
                                                              & (_df_rankmap_data_append["Acc"] >= scorefilter_acc_min)
                                                              & (_df_rankmap_data_append["Acc"] < scorefilter_acc_max)
                                                              & (_df_rankmap_data_append["Rank"] >= scorefilter_rank_min)
                                                              & (_df_rankmap_data_append["Rank"] < scorefilter_rank_max)
                                                              & (_df_rankmap_data_append["Miss"] + _df_rankmap_data_append["Bad"] >= scorefilter_miss_min)
                                                              & (_df_rankmap_data_append["Miss"] + _df_rankmap_data_append["Bad"] < scorefilter_miss_max)
                                                              & (_df_rankmap_data_append['Modifiers'] != 'NF')
                                                              ]

            if not_fc_is_enable:
                _df_filtered_playlist = _df_filtered_playlist[(1 == 1)
                                                              & (_df_rankmap_data_append['FC'] != 'FC')
                                                              ]

            df_playlist = df_playlist.append(_df_not_cleared_playlist)
            df_playlist = df_playlist.append(_df_filtered_playlist)

            # playlist化
            if len(df_playlist) > 0:
                songs = []
                for i, x in df_playlist.iterrows():
                    songs += [{
                        "songName": x["SongName"],
                        "levelAuthorName": x["LevelAuthor"],
                        "hash": x["Hash"],
                        "levelid": f"custom_level_{x['Hash']}",
                        "difficulties": [
                            {
                                "characteristic": "Standard",
                                "name": x["Difficulty"]
                            }
                        ]
                    }]

                _img_url = config['image_path']

                playlist = {
                    "playlistTitle": config['list_name'],
                    "playlistAuthor": "hatopop",
                    "songs": songs, "image": image_file_to_base64(_img_url)
                }

                song_playlist_path = r"{}/{}.json".format(
                    self.playlist_path, config['list_name'])

                with open(song_playlist_path, "w") as f:
                    json.dump(playlist, f)

                self.logger.info("Playlist: {}, Count:{}".format(
                    song_playlist_path, len(df_playlist)))
        self.logger.info(
            "<<Playlist creation in working directory complete.>>")
        return

    def clean_playlist(self):
        """ 作業ディレクトリからPlaylistを削除します
        """
        self.logger.info('Delete playlist in working directory.')
        cnt = 0
        for level_i in range(13):
            song_playlist_path = r"{}/task_{:02d}.json".format(
                self.playlist_dir, level_i)
            try:
                os.remove(song_playlist_path)
                cnt += 1
            except:
                self.logger.debug("{} は存在していません.".format(song_playlist_path))
        self.logger.info(
            'Playlist deletion in working directory complete. count:{:,} '.format(cnt))
        return

    def clean_playlist_json(self, input_dir, playlist_dir):
        """ 作業ディレクトリとPlaylistディレクトリからMyBSList関連のPlaylistを削除します
        """
        self.logger.info(
            'Clean playlist in work & playlists directory for MyBSList.')
        cnt = 0

        files = os.listdir(input_dir)
        workdir_count = 0
        playlistdir_count = 0
        for file in files:
            input_file = os.path.join(input_dir, file)
            playlist_file = os.path.join(playlist_dir, file)
            shutil.copy2(input_file, playlist_dir)
            try:
                os.remove(input_file)
                workdir_count += 1
            except:
                self.logger.debug("{} does not exists.".format(input_file))

            try:
                os.remove(playlist_file)
                playlistdir_count += 1
            except:
                self.logger.debug("{} does not exists.".format(playlist_file))

        self.logger.info(
            'Playlist clean in working & playlists directory complete. count:{:,}, {:,}'.format(workdir_count, playlistdir_count))
        return

    def copy_to_playlist(self, input_dir, playlist_dir):
        """ 解凍したranked_all をplaylistフォルダに展開し上書きします。
        """
        self.logger.info(
            "Copy and paste the playlists into the playlists directory.")
        files = os.listdir(input_dir)
        self.logger.debug("処理対象は {} 件です。".format(len(files)))
        count = 0
        for file in files:
            input_file = os.path.join(input_dir, file)
            shutil.copy2(input_file, playlist_dir)
            count += 1

        self.logger.info(
            "{} playlists have been completed.:{}".format(count, playlist_dir))

    def func_mode(self, x):
        if x == "SoloStandard":
            return "Standard"
        else:
            return x

    def func_fc(self, x):
        if x:
            return "FC"
        else:
            return "-"


def main():
    # configの取得
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    mybstasks = MyBSList(config)
    mybstasks.process()


if __name__ == '__main__':
    main()
