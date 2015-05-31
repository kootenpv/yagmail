import yagmail
import itertools

def getCombinations(yag):
    tos = (None, (yag.user), [yag.user, yag.user], {yag.user : 'me', yag.user + '1' : 'me'}) 
    subjects = ('subj', ['subj'], ['subj', 'subj1']) 
    contents = (None, ['body'], ['body', 'body1', '<h2><center>Text</center></h2>',
             'http://github.com/kootenpv/yagmail', 'body', 'http://tinyurl.com/nwe5hxj']) 
    results = []
    for x in itertools.product(tos, subjects, contents):
        options = {y : z for y,z in zip(['to', 'subject', 'contents'], x)}
        options['previewOnly'] = True
        options['useCache'] = True
        results.append(options)
    return results        

def previewAll():
    """ 
    Tests are only going to pass for "me" <kootenpv@gmail> at this point. 
    I very much will change that in the future
    """
    yag = yagmail.Connect() 
    mail_combinations = getCombinations(yag)
    passed = 0
    failed = 0
    for combination in mail_combinations:
        try: 
            yag.send(**combination)
            passed += 1
        # pylint: disable=broad-except
        # Ignoring broad except because I just want to see all the errors    
        except Exception as e:
            failed += 1
            print(e)
            print(combination)
    print('{} tests passed, {} failed'.format(passed, failed))

if __name__ == '__main__':
    previewAll()  
      
