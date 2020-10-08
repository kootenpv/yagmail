""" Testing module for yagmail """
import itertools
from yagmail import SMTP
from yagmail import raw, inline


def get_combinations(yag):
    """ Creates permutations of possible inputs """
    tos = (
        None,
        (yag.user),
        [yag.user, yag.user],
        {yag.user: '"me" <{}>'.format(yag.user), yag.user + '1': '"me" <{}>'.format(yag.user)},
    )
    subjects = ('subj', ['subj'], ['subj', 'subj1'])
    contents = (
        None,
        ['body'],
        ['body', 'body1', '<h2><center>Text</center></h2>', u"<h1>\u2013</h1>"],
        [raw("body")],
        [{"a": 1}],
    )
    results = []
    for row in itertools.product(tos, subjects, contents):
        options = {y: z for y, z in zip(['to', 'subject', 'contents'], row)}
        options['preview_only'] = True
        results.append(options)

    return results


def test_one():
    """ Tests several versions of allowed input for yagmail """
    yag = SMTP(smtp_skip_login=True, soft_email_validation=False)
    mail_combinations = get_combinations(yag)
    for combination in mail_combinations:
        print(yag.send(**combination))
