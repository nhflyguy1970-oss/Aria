# Source Generated with Decompyle++
# File: journal_quotes.cpython-312.pyc (Python 3.12)

'''Daily quotes — Stoic, Native American, and Tai Chi traditions.'''
from __future__ import annotations
from datetime import date
TRADITIONS = ('stoic', 'native_american', 'tai_chi')
QUOTES: 'dict[str, list[dict[str, str]]]' = {
    'stoic': [
        {
            'text': 'You have power over your mind — not outside events. Realize this, and you will find strength.',
            'author': 'Marcus Aurelius' },
        {
            'text': 'We suffer more often in imagination than in reality.',
            'author': 'Seneca' },
        {
            'text': 'It is not that we have a short time to live, but that we waste much of it.',
            'author': 'Seneca' },
        {
            'text': 'If it is not right, do not do it; if it is not true, do not say it.',
            'author': 'Marcus Aurelius' },
        {
            'text': 'The best revenge is not to be like your enemy.',
            'author': 'Marcus Aurelius' },
        {
            'text': 'No man is free who is not master of himself.',
            'author': 'Epictetus' },
        {
            'text': 'Make the best use of what is in your power, and take the rest as it happens.',
            'author': 'Epictetus' },
        {
            'text': 'Wealth consists not in having great possessions, but in having few wants.',
            'author': 'Epictetus' },
        {
            'text': 'Difficulties strengthen the mind, as labor does the body.',
            'author': 'Seneca' },
        {
            'text': 'Begin at once to live, and count each separate day as a separate life.',
            'author': 'Seneca' },
        {
            'text': 'The happiness of your life depends upon the quality of your thoughts.',
            'author': 'Marcus Aurelius' },
        {
            'text': 'He who fears death will never do anything worth of a living man.',
            'author': 'Seneca' }],
    'native_american': [
        {
            'text': 'We do not inherit the earth from our ancestors; we borrow it from our children.',
            'author': 'Native American proverb' },
        {
            'text': 'Listen to the wind — it talks. Listen to the silence — it speaks. Listen to your heart — it knows.',
            'author': 'Native American proverb' },
        {
            'text': 'Treat the earth well. It was not given to you by your parents; it was loaned to you by your children.',
            'author': 'Native American proverb' },
        {
            'text': 'The soul would have no rainbow if the eyes had no tears.',
            'author': 'Native American proverb' },
        {
            'text': "Tell me a fact and I'll learn. Tell me a truth and I'll believe. Tell me a story and it will live in my heart forever.",
            'author': 'Native American proverb' },
        {
            'text': 'Certain things catch your eye, but pursue only those that capture your heart.',
            'author': 'Native American proverb' },
        {
            'text': 'When we show our respect for other living things, they respond with respect for us.',
            'author': 'Native American proverb' },
        {
            'text': 'Walk lightly in the spring; Mother Earth is pregnant.',
            'author': 'Native American proverb' },
        {
            'text': 'Seek wisdom, not knowledge. Knowledge is of the past; wisdom is of the future.',
            'author': 'Native American proverb' },
        {
            'text': 'The frog does not drink up the pond in which it lives.',
            'author': 'Native American proverb' },
        {
            'text': 'Grown men can learn from very little children — for the hearts of little children are pure.',
            'author': 'Black Elk' },
        {
            'text': 'It is better to have less thunder in the mouth and more lightning in the hand.',
            'author': 'Native American proverb' }],
    'tai_chi': [
        {
            'text': 'Be still like a mountain; move like a great river.',
            'author': 'Tai Chi principle' },
        {
            'text': 'When the mind is calm, the body is relaxed. When the body is relaxed, energy flows.',
            'author': 'Tai Chi teaching' },
        {
            'text': 'Soft overcomes hard; slow overcomes fast.',
            'author': 'Tai Chi principle' },
        {
            'text': 'The root is in the feet; the power is in the legs; the direction is in the waist; the expression is in the fingers.',
            'author': 'Tai Chi classic' },
        {
            'text': 'Seek stillness in movement, and movement in stillness.',
            'author': 'Tai Chi teaching' },
        {
            'text': 'Four ounces deflect a thousand pounds.',
            'author': 'Tai Chi classic' },
        {
            'text': 'The body follows the mind; the mind follows the breath.',
            'author': 'Tai Chi teaching' },
        {
            'text': 'Do not use force against force; yield and redirect.',
            'author': 'Tai Chi principle' },
        {
            'text': 'Practice is the path; patience is the companion.',
            'author': 'Tai Chi teaching' },
        {
            'text': 'Balance is not something you find — it is something you create.',
            'author': 'Tai Chi teaching' },
        {
            'text': 'Empty your cup so that it may be filled.',
            'author': 'Zen / martial teaching' },
        {
            'text': 'In every movement, seek harmony between heaven and earth.',
            'author': 'Tai Chi classic' }] }

def daily_quote(day = None):
    '''Deterministic daily quote — rotates tradition by day, quote by date hash.'''
    d = date.fromisoformat(day) if day else date.today()
    ordinal = d.toordinal()
    tradition = TRADITIONS[ordinal % len(TRADITIONS)]
    pool = QUOTES[tradition]
    pick = pool[ordinal % len(pool)]
    return {
        'text': pick['text'],
        'author': pick['author'],
        'tradition': tradition,
        'tradition_label': tradition.replace('_', ' ').title(),
        'date': d.isoformat() }

