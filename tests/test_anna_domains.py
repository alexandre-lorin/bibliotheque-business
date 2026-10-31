import unittest

import anna_domains

A = 'https://annas-archive.gl'
B = 'https://annas-archive.pk'
C = 'https://annas-archive.gd'


class DomainSelectionTests(unittest.IsolatedAsyncioTestCase):
    async def select(self, states, candidates=None, discoveries=None, **options):
        self.called = []
        async def probe(base):
            self.called.append(base)
            return {'base': base, 'status': states.get(base, 'site_unavailable'), 'announced': []}
        async def discover():
            return discoveries or []
        return await anna_domains.select(A, candidates or [A, B], probe, discover, **options)

    async def test_failed_domain_falls_back_to_available_catalogue(self):
        result = await self.select({A: 'site_unavailable', B: 'homepage_available'})
        self.assertEqual(result['selected'], B)
        self.assertEqual(self.called, [A, B])

    async def test_parked_domain_falls_back(self):
        result = await self.select({A: 'domain_parked', B: 'homepage_available'})
        self.assertEqual(result['selected'], B)

    async def test_captcha_quota_and_access_denial_never_rotate_domains(self):
        for status in anna_domains.HARD_STOPS:
            result = await self.select({A: status, B: 'homepage_available'})
            self.assertIsNone(result['selected'])
            self.assertEqual(result['selection_block'], status)
            self.assertEqual(self.called, [A])

    async def test_explicit_diagnostic_does_not_select_after_restriction(self):
        result = await self.select({A: 'captcha_required', B: 'homepage_available'}, check_all=True)
        self.assertEqual(len(result['checked']), 2)
        self.assertIsNone(result['selected'])
        self.assertEqual(result['selection_block'], 'captcha_required')

    async def test_directory_discovers_new_domain_only_after_failures(self):
        result = await self.select({A: 'site_unavailable', B: 'domain_parked', C: 'homepage_available'}, discoveries=[C])
        self.assertEqual(result['selected'], C)
        self.assertEqual(self.called, [A, B, C])

    async def test_no_infinite_retry_and_candidate_limit(self):
        result = await self.select({}, discoveries=[A, B, C], maximum=2)
        self.assertEqual(len(result['checked']), 2)
        self.assertIsNone(result['selected'])

    async def test_untrusted_redirect_is_not_used_for_fallback(self):
        result = await self.select({A: 'untrusted_redirect', B: 'homepage_available'})
        self.assertIsNone(result['selected'])
        self.assertEqual(self.called, [A])


class CandidateTests(unittest.TestCase):
    def test_only_exact_public_service_domains_are_accepted(self):
        actual = anna_domains.candidates_from_links([
            A, A + '/faq?x=1', B, 'https://annas-archive.gl.evil.example',
            'http://annas-archive.gl', 'https://login.annas-archive.gl',
            'https://user:password@annas-archive.gd', 'https://127.0.0.1',
        ])
        self.assertEqual(actual, [A, B])


if __name__ == '__main__':
    unittest.main()
