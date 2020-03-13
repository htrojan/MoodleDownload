
from moodle import *
from getpass import getpass

m = Moodle()

if 'load' in sys.argv:
    print('Loading saved session...')
    m.load_session()
    print('Done')
else:
    user = input('Username: ')
    password = getpass('Password: ')
    print('Logging in...')
    m.login(user, password)
    print('Done')

# save session only if argument is given for security reasons
if 'save' in sys.argv:
    m.save_session()

# 10 is just an arbitrary limit. It's the default requested from the
# moodle javascript code
courses = m.load_courses(course_limit=10)

for course in courses:
    prefix = course["shortname"]
    name = course["fullname"]
    course_id = course["id"]
    print(f'Course: {name}')
    # Store contents of course in folder with name 'prefix'
    # Fix not allowed folder names (linux only, windows folder names are a mess)
    # Not allowed are slashes '/'
    prefix.replace('/', 's')
    
    if not os.path.exists(prefix):
        os.mkdir(prefix)

    course_page = m.load_course_page(course_id)
    for id in extract_content_ids_iter(course_page):
        m.download_content(id, path_prefix=prefix)
        # Moodle servers are very, very volatile. 
        # Don't overheat them
        time.sleep(.4)
