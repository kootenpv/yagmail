""" Testing module for yagmail """

import itertools
import sys
from os import path


sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from yagmail import SMTP


def get_combinations(yag):
    """ Creates permutations of possible inputs """
    tos = (None, (yag.user), [yag.user, yag.user],
           {yag.user: 'me', yag.user + '1': 'me'})
    subjects = ('subj', ['subj'], ['subj', 'subj1'])
    contents = (None, ['body'], ['body', 'body1', '<h2><center>Text</center></h2>'])
    results = []
    for row in itertools.product(tos, subjects, contents):
        options = {y: z for y, z in zip(['to', 'subject', 'contents'], row)}
        options['preview_only'] = True
        options['use_cache'] = True
        results.append(options)

    return results


def test_one():
    """ Tests several versions of allowed input for yagamail """
    yag = SMTP(smtp_skip_login=True)
    mail_combinations = get_combinations(yag)
    for combination in mail_combinations:
        print(yag.send(**combination))
