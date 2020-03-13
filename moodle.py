import mechanize
import sys, logging
import re
import json
import time
import os
# Debugging only
# logger = logging.getLogger('mechanize')
# logger.addHandler(logging.StreamHandler(sys.stdout))
# logger.setLevel(logging.DEBUG)


class Moodle:
    def __init__(self):
        self.cj = mechanize.LWPCookieJar()
        opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(self.cj))
        mechanize.install_opener(opener)
        self.br = mechanize.Browser()
        self.br.set_cookiejar(self.cj)
        self.sessionkey = 'None'
        self.br.set_header('User-Agent', value='Mozilla/5.0 (X11; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0')
        # self.br.set_debug_http(True)
        self.br.set_debug_redirects(True)

    def login(self, user, passwd):
        print('Logging in')
        # how many times the connection has failed
        self.open_url("https://sso.itmc.tu-dortmund.de/openam/UI/Login?goto=http://moodle.tu-dortmund.de/login")

        tries = 0
        while (self.br.title() is not None and "Anmeldung" in str(self.br.title()) and tries < 5):
            time.sleep(0.5)
            try:
                self.__try_login(user, passwd)
            except mechanize.HTTPError as e:
                error = True
                print(f'Error while connecting. Code: {e.code}')
                #possible redirect after error code. So new call to login page is needed
                self.open_url("https://sso.itmc.tu-dortmund.de/openam/UI/Login?goto=http://moodle.tu-dortmund.de/login")

        # Login was successfull. Now wait before accessing personal moodle site.
        # We don't want to be intrusive
        time.sleep(1.2)
        if self.br.title is not None and "zentrale Anmeldeseite" in str(self.br.title()):
            self.open_url("https://moodle.tu-dortmund.de/")

        answer = self.br.response().read()

        # Moodle needs a variable called 'sessionkey' that is only transmitted through the javascript code of the website.
        # It's different every time and is required alongside the session cookies to make requests to the moodle backend.
        search = (r'(.*)(<script type="text/javascript">.*"sesskey":"(.*?)".*</script>)(.*)')
        result = re.match(search, str(answer), re.DOTALL)
        self.sessionkey = result.group(3)
        print(f'Sessionkey: {self.sessionkey}')


    # Returns a json object returned by the moodle backend representing the 10 recently accessed courses
    def load_courses(self, course_limit=10):
        # Forge ajax request with header and json parameters copied from firefox network debug window 
        header = {
            'Accept':'application/json, text/javascript, */*; q=0.01',
            'Accept-Enconding':'gzip, deflate, br',
            'Content-Type':'application/json',
            'Origin':'https://moodle.tu-dortmund.de',
            'Referer':'https://moodle.tu-dortmund.de/my',
            'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0',
            'X-Requested-With':'XMLHttpRequest',
        }
        json_data = json.loads(r'[{"index":0,"methodname":"core_course_get_recent_courses","args":{"limit":' + str(course_limit) + r'}}]')
        url = f'https://moodle.tu-dortmund.de/lib/ajax/service.php?sesskey={self.sessionkey}&info=core_course_get_recent_courses'

        req = mechanize.Request(url, data=json.dumps(json_data), headers=header, method="POST")
        self.br.open(req)
        string = self.br.response().get_data().decode("utf-8")
        return json.loads(string)[0]["data"]

    def load_course_page(self, id):
        self.open_url(f'https://moodle.tu-dortmund.de/course/view.php?id={id}')
        return self.br.response().read().decode("utf-8")

    def download_content(self, id, path_prefix=''):
        self.open_url(f'https://moodle.tu-dortmund.de/mod/resource/view.php?id={id}')
        response = self.br.response()
        print(f'Content Url: {response.geturl()}')
        f = response.get('Content-Disposition', default=None)
        filename = re.match(r'.*filename="(.*?)"', response.get('Content-Disposition', default=None)).group(1)
        self.retrieve_url(response.geturl(), filename=(path_prefix + '/' +  filename))

    def retrieve_url(self, url, filename):
        for i in range(10):
            try:
                self.br.retrieve(url, filename=filename)
                break
            except mechanize.HTTPError as e:
                print(f'Error while connecting. Code: {e.code}')
                if i is 9:
                    raise Exception('Fatal connection error')
                time.sleep(2)
                continue

    def save_session(self):
        self.cj.save("session/cookies", ignore_discard=True, ignore_expires=True)
        with open('session/sessionkey.txt', 'w') as file:
            file.write(self.sessionkey)

    def load_session(self):
        self.cj.load('session/cookies', ignore_discard=True, ignore_expires=True)
        with (open('session/sessionkey.txt', 'r')) as file:
            self.sessionkey = file.read()

    def __try_login(self, user, passwd):
        print('Anmeldeversuch...')
        self.br.select_form(nr=0)
        self.br.form['IDToken1'] = user
        self.br.form['IDToken2'] = passwd
        self.br.submit()

# Trys to open the given url 5 times with delay of 0.5 seconds inbetween
    def open_url(self, url):
        for i in range(10):
            try:
                self.br.open(url)
                break
            except mechanize.HTTPError as e:
                # print(f'Error while connecting. Code: {e.code}')
                if i is 9:
                    raise Exception('Fatal connection error')
                time.sleep(2)
                continue

# Takes valid moodle course page html as input and extracts all resource ids
def extract_content_ids_iter(course_page):
    search = (r'(\W*)(<a.*?href="https://moodle.tu-dortmund.de/mod/resource/view.php\?id=(.*?)">(.*?)</a>)(\W*)')
    re.finditer(search, course_page, re.DOTALL)
    for match in re.finditer(search, course_page, re.DOTALL):
        yield match.group(3)
