import warnings
warnings.filterwarnings("ignore")
import os
import shutil
import pandas as pd
from pandas import json_normalize
import json
from datetime import datetime
#from dateutil import tz
from tqdm import tqdm
import requests
import math
import base64
import configparser
from distutils.util import strtobool
import libs.playlist_downloader as pl

# ---------------------------------------
# 列情報の設定
# ---------------------------------------
# Player Infoの記録用列 (TotalFC, RankedFCは別途結合)
cols_info =["name","country","pp","rank","countryRank","role","TotalScore","RankedScore","AveRankedAcc"
    ,"TotalPlay","RankedPlay","ReplayWatched","ScoreDate","TotalFC","RankedFC"
    ,"TotalPlayRank","TotalPlayJPRank" ,"RankedPlayRank","RankedPlayJPRank","TotalScoreRank" 
    ,"TotalScoreJPRank","RankedScoreRank","RankedScoreJPRank" ,"AveRankedAccRank","AveRankedAccJPRank"]

# Score用列
cols_score =["Song","Level","Stars","Acc","AccRank","FC","Rank","PP","Miss","Bad","Combo","Score","Difficulty"
        ,"Play","DailyPlay","Bpm","Duration","Notes",'Nps',"Njs","Bombs","Obstacles",'Upvotesratio' 
        ,"Upvotes","Downvotes","Ranked","Days","Months","Tags"]

# Acc再計算用列
cols_recalq = ['Hash','SongName','Difficulty', 'Stars', 'Notes', 'Acc', 'AccRecalq', 'AccDiff','AccRank', 
        'AccRankRecalq', 'MaxScore','MaxScoreRecalq','MaxScoreDiff','Score', 'Miss', 'Combo',]

# RankedMap(BeatSaver)結合用列
cols_rankedmap = ['Hash', 'Difficulty', 'Upvotesratio', 'Nps', 'Tags' ]

cols_playlist = ['Hash', 'SongName', 'SongAuthor', 'LevelAuthor', 'Difficulty', 'Notes',
            'Characteristic','Level', 'Stars', 'Maxscore', 'Acc', 'Score', 'Bad', 'Miss', 
            'PP','Rank','Modifiers', 'DateUtc','Date', 'Days', 'FC']

class MyBSTasks(pl.PlaylistDownloader):
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.player_id = config['param']['player_id']
        self.latest = int(config['param']['latest'])
        self.page_count = int(config['param']['page_count'])
        self.acc_recalq_override_is_enable = strtobool(config['param']['acc_recalq_override_is_enable'])
        self.saved_player_score_is_enable = strtobool(config['param']['saved_player_score_is_enable'])
        self.ranked_song_from_leaderboard_is_enable = strtobool(config['param']['ranked_song_from_leaderboard_is_enable'])

        self.ss_plus_is_enable = strtobool(config['param']['ss_plus_is_enable'])
        self.ss_plus_val = int(config['param']['ss_plus_val'])
        self.ss_plus = "SS+{}".format(self.ss_plus_val)
        self.ss_plus_rate = "SS+{}-Rate".format(self.ss_plus_val)

        self.data_path = config['param']['work_dir'] #self.work_dir

        ## rankedmapdata_url: ランク譜面データのcsvのURLです.らっきょさんデータ. 
        self.rankedmapdata_url = config['param']['rankedmapdata_url']#'https://api.github.com/repos/rakkyo150/RankedMapData/releases'

        # player情報の親フォルダ(data_pathの子フォルダ)
        self.player_path = r"{}/players_data/{}".format(self.data_path, self.player_id)

        ## playerinfoの保存先
        self.player_info_path = r"{}/player_info_{}.csv".format(self.player_path, self.player_id)
        ## playerのscore関連保存先
        self.player_score_path = r"{}/scores_full_{}.csv".format(self.player_path, self.player_id)
        self.player_ranked_path = r"{}/scores_ranked_{}.csv".format(self.player_path, self.player_id)
        self.player_score_pickle_path = r"{}/scores_ranked_{}.pkl".format(self.player_path, self.player_id)

        ## 曲情報の保存先
        self.song_list_path = r"{}/song_list_full.csv".format(self.data_path)
        self.song_ranked_path = r"{}/song_ranked.csv".format(self.data_path)

        # levelclearランク除外関連パス
        self.level_cleared_path = r"{}/level_cleared_{}.csv".format(self.player_path, self.player_id)

        # playlistの保存
        self.playlist_path = r"{}/playlists".format(self.data_path)
        
        # タイムゾーンの設定
        self.tz_ja = pd.Timestamp(datetime.now()).tz_localize('UTC').tz_convert('Asia/Tokyo')


    def process(self):
        """ 一連の処理を実行します.
        """
        self.set_logger()
        self.logger.info("---------------------------------")
        self.logger.info("作業を開始します.")
        try:
            self.create()
            _, self.RangeCount = self.get_player_info()
            df_rankmap_data = self.get_ranked_song_data()
            df_rankmap_data = self.get_ranked_song_data_from_leaderboard(df_rankmap_data)
            df_scores = self.get_player_score_data(self.RangeCount, df_rankmap_data)
            df_scores = self.recalq_accuracy(df_scores)
            df_rankmap_data_append = self.merge_scores_ranked(df_rankmap_data, df_scores)
            self.clean_playlist()
            self.create_playlist(df_rankmap_data_append, self.config)
            self.copy_to_playlist(self.playlist_path, self.playlist_dir)
            if self.clean_flag:
                self.clean()
        except:
            self.logger.error("errorが発生しました.", exc_info=True)
        self.logger.info("作業が完了しました.")
        self.logger.info("---------------------------------")

    def create(self):
        """_作業ディレクトリを作成します_
        """
        self.logger.info("作業ディレクトリを作成します.")

        ## データ大元のフォルダ作成
        if os.path.exists(self.data_path) == False:
            self.logger.info('MyBeatSaberAnalytics用のデータ格納フォルダをGoogle Driveに新規作成します.')
            self.logger.info('データ格納フォルダ:{}'.format(self.data_path))     
            os.makedirs(self.data_path, exist_ok=True)
            self.logger.info('作成が完了しました.')         

        ## データ大元のフォルダ作成
        if os.path.exists(self.player_path) == False:
            self.logger.info('PlayerID:{}用のデータ格納フォルダを新規作成します.'.format(self.player_id))
            self.logger.info('playerフォルダ:{}'.format(self.player_path))     
            self.logger.info('作成が完了しました.')         
            os.makedirs(self.player_path, exist_ok=True)

        ## プレイヤー用のフォルダ作成
        if os.path.exists(self.playlist_path) == False:
            self.logger.info('Playlist格納用のフォルダを新規作成します.')
            self.logger.info('Playlist格納フォルダ:{}'.format(self.playlist_path))     
            os.makedirs(self.playlist_path, exist_ok=True)
            self.logger.info('作成が完了しました.')
        self.logger.info("作業ディレクトリの作成が完了しました. path:{}".format(self.data_path))
        return

    def get_player_info(self):
        """_プレイヤー情報を取得します_

        Returns:
            _df_info : DataFrame
                プレイヤー情報のDataFrameです.
            RangeCount : int
                ScoreSaberのPage数です.
        """
        self.logger.info('プレイヤー情報を取得します.')
        url = r"https://scoresaber.com/api/player/{}/full".format(self.player_id)
        response = requests.get(url)
        res_data = response.json()
        _df_info = json_normalize(res_data)

        _df_info["TotalScore"] = _df_info["scoreStats.totalScore"]
        _df_info["RankedScore"] = _df_info["scoreStats.totalRankedScore"]
        _df_info["AveRankedAcc"] = _df_info["scoreStats.averageRankedAccuracy"]
        _df_info["TotalPlay"] = _df_info["scoreStats.totalPlayCount"]
        _df_info["RankedPlay"] = _df_info["scoreStats.rankedPlayCount"]
        _df_info["ReplayWatched"] = _df_info["scoreStats.replaysWatched"]
        _df_info["ScoreDate"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        _df_info["ScoreDateUtc"] = pd.to_datetime(_df_info['ScoreDate'], utc=True)
        _df_info_idx = _df_info.set_index("ScoreDateUtc")
        _df_info["ScoreDateJa"] = _df_info_idx.index.tz_convert("Asia/Tokyo")

        TotalPlay = _df_info["TotalPlay"][0]
        RankedPlay = _df_info["RankedPlay"][0]
        RangeCount = math.ceil(TotalPlay / self.page_count) + 1
        self.logger.info("Player情報の取得が完了しました. {}, 総プレイ数:{:,}, ランク譜面プレイ数:{:,}, ページ数:{:,}".format(_df_info["name"][0], TotalPlay, RankedPlay,RangeCount))
        return _df_info, RangeCount

    def get_ranked_song_data(self):
        """_ランク譜面の曲情報データフレームを取得します._

        Returns:
            df_rankmap_data : DataFrame
        """
        self.logger.info('ランク譜面のデータを取得します.')
        headers = {
            'Accept': 'application/vnd.github.v3+json',
        }

        response = requests.get(self.rankedmapdata_url, headers=headers)

        data = response.json()

        # 最新releaseのcsvのurl取得
        url_rankmap_data = data[0]["assets"][0]["browser_download_url"]

        file_name = os.path.join(self.data_path, os.path.basename(url_rankmap_data))
        result = requests.get(url_rankmap_data, stream=True)
        if result.status_code == 200:
            with open(file_name, 'wb') as file:
                result.raw.decode_content = True
                shutil.copyfileobj(result.raw, file)

        df_rankmap_data = pd.read_csv(file_name)
        df_rankmap_data = df_rankmap_data[[x for x in df_rankmap_data.columns if not x.startswith("Unnamed")]]
        df_rankmap_data["hash"] = df_rankmap_data["hash"].str.upper()

        df_rankmap_data = df_rankmap_data.rename(columns=lambda x: x.capitalize())

        df_rankmap_data.rename(columns={
                                "Songname":"SongName",
                                "Songsubname":"SongSub",
                                "Songauthorname":"SongAuthor",
                                "Levelauthorname":"LevelAuthor"
                            }, inplace=True)

        # 準備
        df_rankmap_data["Song"] = df_rankmap_data["SongName"] + " / " + df_rankmap_data["SongAuthor"] + " [" + df_rankmap_data["LevelAuthor"] + "]"
        df_rankmap_data["Level"] = df_rankmap_data["Stars"].astype("int")
        df_rankmap_data["LevelStr"] = df_rankmap_data["Level"].astype("str")
        self.logger.info('ランク譜面のデータ取得が完了しました. path:{}, count:{}'.format(file_name, len(df_rankmap_data["Hash"])))
        return df_rankmap_data

    def get_ranked_song_data_from_leaderboard(self, _df_rankmap_data):
        """_ScoreSaber LeaderBoardからランク譜面データフレームを再取得します._
            この処理は全譜面数が一致しない場合に限ります.

        Args:
            _df_rankmap_data (DataFrame): ランク譜面データフレーム

        Returns:
            _df_rankmap_data : DataFrame ランク譜面データフレーム
        """
        self.logger.info('LeaderBoardからランク譜面数を照合します.')

        url = r"https://scoresaber.com/api/leaderboards?ranked=true&page=1&withMetadata=true"
        response = requests.get(url)
        total_count_from_leaderboard = response.json()['metadata']['total']
        level_count_page = response.json()['metadata']['itemsPerPage']
        scoresaber_ranked_page_count = math.ceil(total_count_from_leaderboard / level_count_page)
        self.logger.info("LeaderBoardのランク譜面数は {:,} です.".format(total_count_from_leaderboard))#, scoresaber_ranked_page_count))
        res_data = response.json()
        df_ranked_songs_from_leaderboard = json_normalize(res_data['leaderboards'])

        if len(_df_rankmap_data["Hash"]) != total_count_from_leaderboard:
            self.logger.info('ランク譜面数が一致しません.再取得を開始します.')
            for i in tqdm(range(2, scoresaber_ranked_page_count+1)):
                url = r"https://scoresaber.com/api/leaderboards?ranked=true&page={}".format(i)
                try:
                    response = requests.get(url)
                    res_data = response.json()
                    df_ranked_songs_from_leaderboard=df_ranked_songs_from_leaderboard.append(json_normalize(res_data['leaderboards']), ignore_index=True)
                except:
                    break

            def func_mode(x):
                if  x == "SoloStandard":
                    return "Standard"
                else:
                    return x

            df_ranked_songs_from_leaderboard['Hash'] = df_ranked_songs_from_leaderboard['songHash'].str.upper()
            df_ranked_songs_from_leaderboard['Song'] = df_ranked_songs_from_leaderboard['songName'] + " " + df_ranked_songs_from_leaderboard['songSubName'] + " / " + df_ranked_songs_from_leaderboard['songAuthorName'] + " [" + df_ranked_songs_from_leaderboard['levelAuthorName'] + "]"
            df_ranked_songs_from_leaderboard['SongName'] = df_ranked_songs_from_leaderboard['songName']
            df_ranked_songs_from_leaderboard['SongSub'] = df_ranked_songs_from_leaderboard['songSubName']
            df_ranked_songs_from_leaderboard['SongAuthor'] = df_ranked_songs_from_leaderboard['songAuthorName']
            df_ranked_songs_from_leaderboard['LevelAuthor'] = df_ranked_songs_from_leaderboard['levelAuthorName']
            df_ranked_songs_from_leaderboard['Mode'] = df_ranked_songs_from_leaderboard['difficulty.gameMode'].apply(func_mode)
            _df_ranked_songs_from_leaderboard = df_ranked_songs_from_leaderboard['difficulty.difficultyRaw'].str.split('_', expand=True)
            _df_ranked_songs_from_leaderboard.columns = ['_','Difficulty', 'Mode']
            df_ranked_songs_from_leaderboard['Difficulty'] = _df_ranked_songs_from_leaderboard['Difficulty']
            df_ranked_songs_from_leaderboard['Stars'] = df_ranked_songs_from_leaderboard['stars']
            df_ranked_songs_from_leaderboard['Level'] = df_ranked_songs_from_leaderboard['Stars'].astype('int')
            df_ranked_songs_from_leaderboard["LevelStr"] = df_ranked_songs_from_leaderboard['Level'].astype('str')
            self.logger.info("RankedSong(ScoreSaber leaderboard):{:,}".format(df_ranked_songs_from_leaderboard["Song"].count()))
            if total_count_from_leaderboard == df_ranked_songs_from_leaderboard["Song"].count():
                ranked_song_from_leaderboard_is_enable = True
            else:
                self.logger.info('ランク譜面数が一致しません.何らかのトラブルが発生しました.')
                return _df_rankmap_data

        else:
            self.logger.info('ランク譜面数が一致しました.再取得処理を完了します.')
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
        self.logger.info('PlayerのScore情報を取得します.')

        if self.saved_player_score_is_enable and os.path.exists(self.player_score_pickle_path):    
            df_scores_pkl = pd.read_pickle(self.player_score_pickle_path)
            _df_scores_pkl = df_scores_pkl.head(0)

            i = 1
            while True:
                url = r"https://scoresaber.com/api/player/{}/scores?sort=recent&page={}&limit={}".format(self.player_id, i, self.page_count)
                try:
                    response = requests.get(url)
                    res_data = response.json()
                    _df_scores_pkl=_df_scores_pkl.append(json_normalize(res_data['playerScores']), ignore_index=True)
                    if df_scores_pkl['score.timeSet'].max() > _df_scores_pkl['score.timeSet'].min():
                        break
                except:
                    break

            _df_scores=df_scores_pkl.append(_df_scores_pkl, ignore_index=True).sort_values("score.timeSet", ascending=False).groupby("score.id").head(1)

        else:
            url = r"https://scoresaber.com/api/player/{}/scores?sort=recent&limit={}".format(self.player_id, self.page_count)
            response = requests.get(url)
            res_data = response.json()
            _df_scores = json_normalize(res_data['playerScores'])

            for i in tqdm(range(2, _RangeCount)):
                url = r"https://scoresaber.com/api/player/{}/scores?sort=recent&page={}&limit={}".format(self.player_id, i, self.page_count)
                try:
                    response = requests.get(url)
                    res_data = response.json()
                    _df_scores=_df_scores.append(json_normalize(res_data['playerScores']), ignore_index=True)
                except:
                    break

        # 未加工データ保存
        _df_scores.to_pickle(self.player_score_pickle_path)

        _df_scores['Song'] = _df_scores['leaderboard.songName'] + " " + _df_scores['leaderboard.songSubName'] + " / " + _df_scores['leaderboard.songAuthorName'] + " [" + _df_scores['leaderboard.levelAuthorName'] + "]"
        _df_scores['SongName'] = _df_scores['leaderboard.songName']
        _df_scores['SongSub'] = _df_scores['leaderboard.songSubName']
        _df_scores['SongAuthor'] = _df_scores['leaderboard.songAuthorName']
        _df_scores['LevelAuthor'] = _df_scores['leaderboard.levelAuthorName']
        _df_scores['Hash'] = _df_scores['leaderboard.songHash'].str.upper()
        _df_scores['Acc'] = _df_scores['score.modifiedScore'] / _df_scores['leaderboard.maxScore'] * 100
        _df_scores['MaxScore'] = _df_scores['leaderboard.maxScore']
        _df_scores['Mode'] = _df_scores['leaderboard.difficulty.gameMode'].apply(self.func_mode)
        __df_scores = _df_scores['leaderboard.difficulty.difficultyRaw'].str.split('_', expand=True)
        __df_scores.columns = ['_','Difficulty', 'Mode']
        _df_scores['Difficulty'] = __df_scores['Difficulty']
        _df_scores['Stars'] = _df_scores['leaderboard.stars']
        _df_scores['Level'] = _df_scores['Stars'].astype('int')
        _df_scores["LevelStr"] = _df_scores['Level'].astype('str')
        _df_scores['Score'] = _df_scores['score.modifiedScore']
        _df_scores['Bad'] = _df_scores['score.badCuts']
        _df_scores['Miss'] = _df_scores['score.missedNotes']
        _df_scores['Combo'] = _df_scores['score.maxCombo']
        _df_scores['PP'] = _df_scores['score.pp']
        _df_scores['PPWeight'] = _df_scores['score.pp'] * _df_scores['score.weight']
        _df_scores['Rank'] = _df_scores['score.rank']
        _df_scores['Modifiers'] = _df_scores['score.modifiers']
        _df_scores['Ranked'] = _df_scores['leaderboard.ranked']
        _df_scores['Qualified'] = _df_scores['leaderboard.qualified']
        _df_scores['Play'] = _df_scores['leaderboard.plays']
        _df_scores['DailyPlay'] = _df_scores['leaderboard.dailyPlays']
        _df_scores['DateUtc'] = pd.to_datetime(_df_scores['score.timeSet'])
        _df_scores_idx = _df_scores.set_index('DateUtc')
        _df_scores['DateJa'] = _df_scores_idx.index.tz_convert('Asia/Tokyo')
        _df_scores['Date'] = _df_scores['DateJa'].dt.date
        _df_scores['Days'] = (self.tz_ja.date() - _df_scores['Date']).dt.days
        _df_scores = _df_scores.set_index('DateJa')
        _df_scores['Months'] = (_df_scores['Days'] / 30).astype('int')
        _df_scores['DaysStr'] = _df_scores['Days'].astype('str')
        _df_scores['MonthsStr'] = _df_scores['Months'].astype('str')
        _df_scores['Latest'] = _df_scores['Days'].apply(self.func_latest)
        _df_scores['AccRank'] = _df_scores['Acc'].apply(self.func_score)
        _df_scores['FC'] = _df_scores['score.fullCombo'].apply(self.func_fc)

        _df_scores = _df_scores[[x for x in _df_scores.columns if not x.startswith("score.")]]
        _df_scores = _df_scores[[x for x in _df_scores.columns if not x.startswith("leaderboard.")]]

        # 改行コード等の除去
        for col in _df_scores.columns:
            try:
                if len(_df_scores[_df_scores[col].str.contains("\n")][[col]]) == 0:
                    continue
                else:
                    _df_scores[col] = _df_scores[col].str.replace("\n","")
            except:
                continue

        for col in _df_scores.columns:
            try:
                if len(_df_scores[_df_scores[col].str.contains("\r")][[col]]) == 0:
                    continue
                else:
                    _df_scores[col] = _df_scores[col].str.replace("\r","")
            except:
                continue


        # RankedMap(らっきょさんのBeatSaverデータ)の情報結合
        _df_scores = _df_scores.reset_index()
        _df_scores = pd.merge(_df_scores, _df_rankmap_data, on=["Hash", "Difficulty"], how="left", suffixes=("", "_y"))
        _df_scores = _df_scores[[x for x in _df_scores.columns if not x.endswith("_y")]]
        _df_scores = _df_scores.set_index("DateJa")

        #Score情報の保存
        _df_scores[(_df_scores['Ranked'] == True)][cols_score].sort_index(ascending=False).to_csv(self.player_ranked_path)
        _df_scores = _df_scores[(_df_scores['Ranked'] == True)].sort_index(ascending=False)
        _df_scores.sort_index(ascending=False).to_csv(self.player_score_path.format(self.player_id))

        self.logger.info('PlayerのScore情報を取得を完了しました. ランク譜面プレイ数は {:,} です.'.format(_df_scores['Play'].count()))
        return _df_scores

    def recalq_accuracy(self, _df_scores):
        """_notes数とcombo数に基づきAccを再計算し、Score情報を上書きします._

        Args:
            _df_scores (_DataFrame_): _Playerのスコア情報のデータフレームです._

        Returns:
            _DataFrame_: _Accを再計算し上書きしたスコア情報のデータフレームです._
        """
        self.logger.info('notes数とcombo数に基づきAccの再計算を開始します.')

        def func_max_score(_notes):
            """ notes数とcombo数に基づいた最大スコアの再計算
            """
            combo_a = 115 * 1
            combo_b = 115 * 2
            combo_c = 115 * 4
            combo_d = 115 * 8

            if  _notes >= 14:
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
        _df_scores['MaxScoreRecalq'] = _df_scores['Notes'].apply(func_max_score)
        _df_scores['AccRecalq'] = _df_scores['Score'] / _df_scores['MaxScoreRecalq'] * 100
        _df_scores['AccRankRecalq'] = _df_scores['AccRecalq'].apply(self.func_score)
        _df_scores['MaxScoreDiff'] = _df_scores['MaxScore'].fillna(0) - _df_scores['MaxScoreRecalq'].fillna(0)
        _df_scores['AccDiff'] = _df_scores['Acc'].fillna(0) - _df_scores['AccRecalq'].fillna(0)

        df_errors = _df_scores[
                    (1==1)
                    &(_df_scores['Ranked'])
                    &(_df_scores['MaxScoreDiff'] != 0)
                    ]

        self.logger.info('Accがゲームと異なる結果が{}件あります.'.format(len(df_errors)))

        if self.acc_recalq_override_is_enable:
            _df_scores.rename(columns={
                                    "MaxScore":"MaxScoreOrg",
                                    "Acc":"AccOrg",
                                    "AccRank":"AccRankOrg"
                                    }, inplace=True)
            _df_scores.rename(columns={
                                    "MaxScoreRecalq":"MaxScore",
                                    "AccRecalq":"Acc",
                                    "AccRankRecalq":"AccRank"
                                    }, inplace=True)
            self.logger.info('Accを再計算した結果を上書きしました.')
        return _df_scores

    def merge_scores_ranked(self,_df_rankmap_data, _df_scores):
        """_結合データを作成します._

        Args:
            _df_rankmap_data (_DataFrame_): _ランク譜面データ_
            _df_scores (_DataFrame_): _プレイヤのランク譜面のスコアデータ_

        Returns:
            _DataFrame_: _結合データ_
        """
        self.logger.info('結合データを作成します.')
        _df_rankmap_data_append = pd.merge(_df_rankmap_data, _df_scores.reset_index(), on=["Hash", "Difficulty"], how="left", suffixes=("", "_y"))[cols_playlist]
        _df_rankmap_data_append = _df_rankmap_data_append[[x for x in _df_rankmap_data_append.columns if not x.endswith("_y")]]
        self.logger.info('結合が完了しました.件数:{:,}'.format(len(_df_rankmap_data_append)))
        return _df_rankmap_data_append

    def create_playlist(self, _df_rankmap_data_append, config):
        """ Playlistを作成
        """
        self.logger.info('作業ディレクトリにPlaylist作成を開始します.')

        def image_file_to_base64(_file_path):
            """ 画像ファイルをBase64エンコードし文字列に変換
            """
            with open(_file_path, "rb") as image_file:
                data = base64.b64encode(image_file.read())

            return "data:image/png;base64,{}".format(data.decode('utf-8'))

        for level_i in range(13):
            star_i = "star{:02d}".format(level_i)
            playlist_is_enable = strtobool(config[star_i]['playlist_is_enable'])
            not_play_is_enable = strtobool(config[star_i]['not_play_is_enable'])
            nf_is_enable = strtobool(config[star_i]['nf_is_enable'])
            not_fc_is_enable = strtobool(config[star_i]['not_fc_is_enable'])
            filtered_is_enable = strtobool(config[star_i]['filtered_is_enable'])
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
            _df_filtered_playlist = _df_rankmap_data_append #.head(0)

            # not played
            if not_play_is_enable:
                _df_not_cleaed_playlist = _df_not_cleaed_playlist.append(_df_rankmap_data_append[(1==1)
                    & (_df_rankmap_data_append["Level"] == level_i)
                    & (_df_rankmap_data_append['Score'].isnull())
                    ])

            # NF
            if nf_is_enable:
                _df_not_cleaed_playlist = _df_not_cleaed_playlist.append(_df_rankmap_data_append[(1==1)
                    & (_df_rankmap_data_append["Level"] == level_i)
                    & (_df_rankmap_data_append['Modifiers'] == 'NF')
                    ])

            if filtered_is_enable or not_fc_is_enable:
                _df_filtered_playlist = _df_rankmap_data_append
            else:
                _df_filtered_playlist = _df_rankmap_data_append.head(0)

            # Filtered
            if filtered_is_enable:
                _df_filtered_playlist = _df_filtered_playlist[(1==1)
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
                _df_filtered_playlist = _df_filtered_playlist[(1==1)
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
                    "songs": songs
                    ,"image": image_file_to_base64(_img_url)
                }

                song_playlist_path = r"{}/task_{:02d}.json".format(self.playlist_path, level_i, datetime.now().strftime("%Y%m%d"))

                with open(song_playlist_path, "w") as f:
                    json.dump(playlist, f)

                self.logger.info("{} Playlistを出力しました. 曲数:{}".format(song_playlist_path, len(df_playlist)))
        self.logger.info("作業ディレクトリにPlaylist作成を完了しました.")
        return

    def clean_playlist(self):
        """ 作業ディレクトリからPlaylistを削除します
        """
        self.logger.info('作業ディレクトリのPlaylistを削除します.')
        cnt = 0
        for level_i in range(13):
            song_playlist_path = r"{}/task_{:02d}.json".format(self.playlist_dir, level_i)
            try:
                os.remove(song_playlist_path)
                cnt += 1
            except:
                self.logger.debug("{} は存在していません.".format(song_playlist_path))
        self.logger.info('作業ディレクトリのPlaylist削除が完了しました. {:,} 件'.format(cnt))
        return


    def func_mode(self, x):
        if  x == "SoloStandard":
            return "Standard"
        else:
            return x

    def func_score(self, x):
        if  x > 100:
            return "-"
        elif x == 100:
            return "SSS"
        elif x >= self.ss_plus_val and self.ss_plus_is_enable:
            return self.ss_plus
        elif x >= 90:
            return "SS"
        elif x >= 80:
            return "S"
        elif x >= 65:
            return "A"
        elif x >= 50:
            return "B"
        elif x >= 35:
            return "C"
        elif x >= 20:
            return "D"
        elif x >= 0:
            return "E"
        else:
            return "-"

    def func_fc(self, x):
        if  x:
            return "FC"
        else:
            return "-"

    def func_latest(self, x):
        if  x <= self.latest:
            return 1
        else:
            return 0

def main():
    # configの取得
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    mybstasks = MyBSTasks(config)
    mybstasks.process()

if __name__ == '__main__':
    main()