from .requester import Requester
from .tools import *

class AZlyrics(Requester):
    """
    Fast and Secure API for AZLyrics.com.

    Attributes:
        title (str): song title.
        artist (str): artist name.
        search_engine (str): search engine used to assist scraping lyrics.
            - currently available: 'google', 'duckduckgo'.
        accuracy (float): used to determine accuracy via jaro algorithm.
        proxies (dict): if you want to use proxy while connecting to 'AZLyrics.com'.
    """
    
    def __init__(self, search_engine='', accuracy=0.6, proxies={}):
        self.title = ''
        self.artist = ''
        self.search_engine = search_engine
        
        self.accuracy = accuracy
        if not 0 < accuracy <= 1:
            self.accuracy = 0.6
        
        self.proxies = proxies

        self.lyrics_history = []
        self.lyrics = ''
        self.songs = {}

    def getLyrics(self, url=None, ext='txt', save=False, path='', sleep=3):
        try:
            time.sleep(sleep)

            link = url

            if not url:
                if not self.artist + self.title:
                    raise ValueError("Both artist and title can't be empty!")
                if self.search_engine:
                    link = googleGet(
                                self.search_engine,
                                self.accuracy,
                                self.get,
                                self.artist,
                                self.title,
                                0,
                                self.proxies
                            )
                    if not link:
                        return 0
                else:
                    link = normalGet(
                                self.artist,
                                self.title,
                                0)

            page = self.get(link, self.proxies)
            if page.status_code != 200:
                if page.status_code == 403:  # Forbidden, likely an IP ban
                    print('IP banned. Switching proxy...')
                    self.proxies = random.choice(self.PROXIES)
                    return self.getLyrics(url=url, ext=ext, save=save, path=path, sleep=sleep)
                elif not self.search_engine:
                    print('Failed to find lyrics. Trying to get link from Google')
                    self.search_engine = 'google'
                    lyrics = self.getLyrics(url=url, ext=ext, save=save, path=path, sleep=sleep)
                    self.search_engine = ''
                    return lyrics
                else:
                    print('Error', page.status_code)
                    return 1

            metadata = [elm.text for elm in htmlFindAll(page)('b')]
            
            if not metadata:
                print('Error', 'no metadata')
                return 1
            
            self.artist = filtr(metadata[0][:-7], True)
            self.title = filtr(metadata[1][1:-1], True)

            lyrics = parseLyric(page)
            self.lyrics = lyrics.strip()

            if lyrics:
                if save:
                    p = os.path.join(
                                    path,
                                    '{} - {}.{}'.format(
                                                    self.title.title(),
                                                    self.artist.title(),
                                                    ext
                                                    )
                                    )
                    
                    with open(p, 'w', encoding='utf-8') as f:
                        f.write(lyrics.strip())
                
                self.lyrics_history.append(self.lyrics)
                return self.lyrics

            self.lyrics = 'No lyrics found :('
            return 2
        
        except Exception as e:
            print('An error occurred:', str(e))
            return 1



    def getSongs(self, sleep=3):
        """
        Retrieve a dictionary of songs with their links.

        Parameters:
            sleep (float): cooldown before next request.  
        
        Returns:
            dict: dictionary of songs with their links.
        """

        if not self.artist:
            raise Exception("Artist can't be empty!")
        
        # Best cooldown is 5 sec
        time.sleep(sleep)
        
        if self.search_engine:
            link = googleGet(
                        self.search_engine,
                        self.accuracy,
                        self.get,
                        self.artist,
                        '',
                        1,
                        self.proxies
                    )
            if not link:
                return {}
        else:
            link = normalGet(
                        self.artist,
                        '',
                        1)
        
        albums_page = self.get(link, self.proxies)
        if albums_page.status_code != 200:
            if not self.search_engine:
                print('Failed to find songs. Trying to get link from Google')
                self.search_engine = 'google'
                songs = self.getLyrics(sleep=sleep)
                self.search_engine = ''
                return songs
            else:
                print('Error',albums_page.status_code)
                return {}
        
        # Store songs for later usage
        self.songs = parseSongs(albums_page)
        return self.songs
