import yagmail
import itertools

def getCombinations(yag):
    tos = (None, (yag.From), [yag.From, yag.From], {yag.From : 'me', yag.From + '1' : 'me'}) 
    subjects = ('subj', ['subj'], ['subj', 'subj1']) 
    contents = (None, ['body'], ['body', 'body1', '/Users/pascal/GDrive/yagmail/yagmail/example.html', '<h2>Text</h2>',
             'http://github.com/kootenpv/yagmail', 'body', '/Users/pascal/GDrive/yagmail/yagmail/sky.jpg', 
             'http://tinyurl.com/nwe5hxj']) 
    results = []
    for x in itertools.product(tos, subjects, contents):
        options = {y : z for y,z in zip(['To', 'Subject', 'Contents'], x)}
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
    z = getCombinations(yag)
    passed = 0
    failed = 0
    for x in z:
        try:
            # pylint: disable=star-args
            yag.send(**x)
            passed += 1
        # pylint: disable=broad-except
        # Ignoring broad except because I just want to see all the errors    
        except Exception as e:
            failed += 1
            print(e)
            print(x)
    print('{} tests passed, {} failed'.format(passed, failed))

if __name__ == '__main__':
    previewAll()  
      
