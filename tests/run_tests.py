import itertools

import sys
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from yagmail import SMTP
yag = SMTP()

def getCombinations():
    tos = (None, (yag.user), [yag.user, yag.user], {yag.user : 'me', yag.user + '1' : 'me'}) 
    subjects = ('subj', ['subj'], ['subj', 'subj1']) 
    contents = (None, ['body'], ['body', 'body1', '<h2><center>Text</center></h2>',
             'http://github.com/kootenpv/yagmail', 'body', 'http://tinyurl.com/nwe5hxj']) 
    results = []
    for x in itertools.product(tos, subjects, contents):
        options = {y : z for y,z in zip(['to', 'subject', 'contents'], x)}
        options['preview_only'] = True
        options['use_cache'] = True
        results.append(options)
        
    return results        

def test_one(): 
    mail_combinations = getCombinations()
    for combination in mail_combinations:
        print(yag.send(**combination))
