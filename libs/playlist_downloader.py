# coding: utf-8
import os
import time
import shutil
import zipfile
from datetime import datetime
from distutils.util import strtobool
#import logging
import traceback
import configparser
# Third party libraries
import requests

from logging import basicConfig, getLogger, INFO, DEBUG, StreamHandler, FileHandler, Formatter
import json
from logging import getLogger
from logging.config import dictConfig

class PlaylistDownloader:
    """ Apluluさん(@aplulu_cat)作成のranked_all.zip をダウンロードし、playlistフォルダに展開するクラスです

        BSRankedPlaylist

        https://github.com/aplulu/bs-ranked-playlist

    """

    def __init__(self, config):
        """ 一連の処理を実行します。
        """
        # "https://github.com/aplulu/bs-ranked-playlist/releases/latest/download/ranked_all.zip"
        self.url = config['param']['url'] 
        # BeatSaber Playlistsのディレクトリ
        self.playlist_dir = config['param']['playlist_dir']
        # 作業ディレクトリ
        self.work_dir = os.path.join(
            config['param']['work_dir'], datetime.now().strftime('%Y%m%d%H%M%S'))
        # 作業ディレクトリ削除フラグ
        self.clean_flag = strtobool(config['param']['clean_flag'])
        # logdir
        self.log_dir = config['param']['log_dir']

    def process(self):
        """ 一連の処理を実行します。
        """
        self.set_logger()
        self.logger.info("---------------------------------")
        self.logger.info("作業を開始します。")
        try:
            self.create()
            self.zipfile_path = self.download(self.url, self.work_dir)
            self.unzipeddir_path = self.unzip(self.zipfile_path)
            self.copy_to_playlist(self.unzipeddir_path, self.playlist_dir)
            if self.clean_flag:
                self.clean()
        except:
            self.logger.error("errorが発生しました。", exc_info=True)
        self.logger.info("作業が完了しました。")
        self.logger.info("---------------------------------")

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
        handler1.setFormatter(Formatter("%(asctime)s - %(levelname)8s - %(message)s"))

        #handler2を作成
        handler2 = FileHandler(filename=log_file)  #handler2はファイル出力
        #handler2.setLevel(INFO)     #handler2はLevel.WARN以上
        handler2.setFormatter(Formatter("%(asctime)s - %(levelname)8s - %(message)s"))

        #loggerに2つのハンドラを設定
        self.logger.addHandler(handler1)
        self.logger.addHandler(handler2)


    def download(self, url, download_dir):
        """ playlist ranked_all.zip をダウンロードします。
        """
        self.logger.info("ダウンロードを開始します")
        file_name = os.path.join(download_dir, os.path.basename(url))
        result = requests.get(url, stream=True)
        if result.status_code == 200:
            with open(file_name, 'wb') as file:
                result.raw.decode_content = True
                shutil.copyfileobj(result.raw, file)
        self.logger.info("ダウンロードが完了しました。:{}".format(file_name))
        return file_name

    def unzip(self, file_name):
        """ ranked_all.zip を解凍します。
        """
        self.logger.info("zipの解凍を開始します。")
        with zipfile.ZipFile(file_name, 'r')as f:
            unziped_dir = file_name.split('.')[0]
            f.extractall(unziped_dir)
        self.logger.info("zipの解凍を完了しました。:{}".format(unziped_dir))
        return unziped_dir

    def copy_to_playlist(self, input_dir, playlist_dir):
        """ 解凍したranked_all をplaylistフォルダに展開し上書きします。
        """
        self.logger.info("PlaylistsディレクトリにPlaylistを配置します。")
        files = os.listdir(input_dir)
        self.logger.debug("処理対象は {} 件です。".format(len(files)))
        count = 0
        for file in files:
            input_file = os.path.join(input_dir, file)
            shutil.copy2(input_file, playlist_dir)
            count += 1

        self.logger.info(
            "{} 件のplaylistの配置が完了しました。:{}".format(count, playlist_dir))

    def create(self):
        """ 作業ディレクトリを作成します。
        """
        self.logger.info("作業ディレクトリを作成します。")
        os.makedirs(self.work_dir)
        self.logger.info("作業ディレクトリの作成が完了しました。:{}".format(self.work_dir))

    def clean(self):
        """ 作業ディレクトリを削除します。
        """
        self.logger.info("作業ディレクトリの削除を開始します。")
        shutil.rmtree(self.work_dir)
        self.logger.info("作業ディレクトリの削除が完了しました。:{}".format(self.work_dir))


def main():
    # configの取得
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')

    # 最新playlistの取得
    playlist = PlaylistDownloader(config)
    playlist.process()


if __name__ == '__main__':
    main()
