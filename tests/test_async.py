import pytest
import asyncio
import itertools
import base64
from yagmail import AsyncSMTP, AIOSMTP, Connection, AsyncConnection, SMTP
from yagmail.utils import raw

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

def test_async_alias():
    assert AIOSMTP is AsyncSMTP
    assert Connection is SMTP
    assert AsyncConnection is AsyncSMTP

def test_async_context_manager():
    async def run():
        async with AsyncSMTP(smtp_skip_login=True, soft_email_validation=False) as yag:
            assert not yag.is_closed
            recipients, msg_string = await yag.send(
                to="test@example.com",
                subject="Test subject",
                contents="Test content",
                preview_only=True
            )
            assert recipients == ["test@example.com"]
            assert "Subject: Test subject" in msg_string
            content_b64 = base64.b64encode(b"Test content").decode("utf-8")
            assert content_b64 in msg_string
        assert yag.is_closed
    asyncio.run(run())

def test_async_combinations():
    async def run():
        yag = AsyncSMTP(smtp_skip_login=True, soft_email_validation=False)
        combinations = get_combinations(yag)
        
        async def run_comb(c):
            recipients, msg_string = await yag.send(**c)
            assert isinstance(recipients, list) or recipients is None
            assert isinstance(msg_string, str)
            
        await asyncio.gather(*(run_comb(c) for c in combinations))
    asyncio.run(run())

def test_async_close_error():
    async def run():
        yag = AsyncSMTP(smtp_skip_login=True, soft_email_validation=False)
        with pytest.raises(ValueError, match="Should be `async with` or use `await aclose\\(\\)`"):
            await yag.close()
    asyncio.run(run())

def test_async_aclose_and_login():
    async def run():
        yag = AsyncSMTP(smtp_skip_login=True, soft_email_validation=False)
        await yag.login()
        assert not yag.is_closed
        await yag.aclose()
        assert yag.is_closed
    asyncio.run(run())

def test_async_send_unsent():
    async def run():
        yag = AsyncSMTP(smtp_skip_login=True, soft_email_validation=False)
        await yag.login()
        yag.unsent.append((["test@example.com"], "Subject: unsent\n\nunsent content"))
        assert len(yag.unsent) == 1
        
        call_count = 0
        async def mock_sendmail(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return {}
            
        yag.smtp.sendmail = mock_sendmail  # type: ignore[assignment]
        await yag.send_unsent()
        assert len(yag.unsent) == 0
        assert call_count == 1
        await yag.aclose()
    asyncio.run(run())
