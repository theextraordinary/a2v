import re


def normalize_token(token: str) -> str:
    t = token.strip().lower()
    t = re.sub(r'^[^\w]+|[^\w]+$', '', t)
    return t


def tokenize(text: str):
    return [t for t in text.split() if t.strip()]


def align_tokens_dp(orig_tokens, corr_tokens):
    """
    Dynamic-programming alignment between orig and corrected tokens.
    Returns a list of ops: (op, i, j)
    op in {'match','replace','delete','insert'}
    i index in orig, j index in corr (or None)
    """
    n = len(orig_tokens)
    m = len(corr_tokens)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        dp[i][0] = i
        back[i][0] = 'delete'
    for j in range(1, m + 1):
        dp[0][j] = j
        back[0][j] = 'insert'

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            o = normalize_token(orig_tokens[i - 1])
            c = normalize_token(corr_tokens[j - 1])
            cost_sub = 0 if o == c else 1

            choices = [
                (dp[i - 1][j] + 1, 'delete'),
                (dp[i][j - 1] + 1, 'insert'),
                (dp[i - 1][j - 1] + cost_sub, 'match' if cost_sub == 0 else 'replace'),
            ]
            best = min(choices, key=lambda x: x[0])
            dp[i][j] = best[0]
            back[i][j] = best[1]

    # backtrace
    ops = []
    i, j = n, m
    while i > 0 or j > 0:
        op = back[i][j]
        if op in ('match', 'replace'):
            ops.append((op, i - 1, j - 1))
            i -= 1
            j -= 1
        elif op == 'delete':
            ops.append((op, i - 1, None))
            i -= 1
        elif op == 'insert':
            ops.append((op, None, j - 1))
            j -= 1
        else:
            break
    ops.reverse()
    return ops


def force_same_length_tokens(orig_tokens, corr_tokens, ops):
    """
    Returns corrected_tokens with same length as orig_tokens.
    Inserts are attached to nearest previous token; deletes keep original token.
    """
    n = len(orig_tokens)
    corr_map = [[] for _ in range(n)]

    last_i = 0
    for op, i, j in ops:
        if op in ('match', 'replace') and i is not None and j is not None:
            corr_map[i].append(j)
            last_i = i
        elif op == 'delete' and i is not None:
            last_i = i
        elif op == 'insert' and j is not None:
            # attach insertion to nearest previous token (or next if none)
            target = last_i if last_i is not None else 0
            if target is None:
                target = 0
            if target >= n:
                target = n - 1
            corr_map[target].append(j)

    corrected = []
    for i in range(n):
        if corr_map[i]:
            corrected.append(corr_tokens[corr_map[i][0]])
        else:
            corrected.append(orig_tokens[i])

    return corrected


def build_sentence_metadata(words, corrected_tokens, sentence_gap_s=0.6):
    """
    Adds sentence_id, pause_before, pause_after to each word using timing gaps and punctuation.
    """
    out = []
    sentence_id = 0
    for i, w in enumerate(words):
        start = float(w['start'])
        end = float(w['end'])
        pause_before = 0.0
        if i > 0:
            pause_before = max(0.0, start - float(words[i - 1]['end']))

        token = corrected_tokens[i] if i < len(corrected_tokens) else w['word']
        prev_token = corrected_tokens[i - 1] if i > 0 else ''

        # start new sentence if long pause or previous ended with punctuation
        if i == 0:
            sentence_id = 0
        else:
            if pause_before >= sentence_gap_s or prev_token.endswith(('.', '?', '!')):
                sentence_id += 1

        # pause_after
        pause_after = 0.0
        if i < len(words) - 1:
            pause_after = max(0.0, float(words[i + 1]['start']) - end)

        out.append({
            'word': token,
            'start': start,
            'end': end,
            'sentence_id': sentence_id,
            'pause_before': pause_before,
            'pause_after': pause_after,
        })
    return out


def compute_pauses(words):
    pauses = []
    for i, w in enumerate(words):
        if i == 0:
            pauses.append(0.0)
        else:
            pauses.append(max(0.0, float(w['start']) - float(words[i - 1]['end'])))
    return pauses


def infer_sentence_starts(words, sentence_gap_s=0.8):
    starts = [0]
    for i in range(1, len(words)):
        gap = max(0.0, float(words[i]['start']) - float(words[i - 1]['end']))
        prev = words[i - 1]['word'] if i > 0 else ''
        if gap >= sentence_gap_s or prev.endswith(('.', '?', '!')):
            starts.append(i)
    return starts


def segment_caption_groups(words, silence_gap_s=0.6, max_words_per_group=3, sentence_gap_s=0.8, avoid_single_trailing_word=True):
    if not words:
        return []

    # Ensure sentence_id exists
    if 'sentence_id' not in words[0]:
        corrected_tokens = [w['word'] for w in words]
        words = build_sentence_metadata(words, corrected_tokens, sentence_gap_s=sentence_gap_s)

    groups = []
    i = 0
    group_id = 0
    n = len(words)
    while i < n:
        # start new group at sentence boundary or long silence
        start_i = i
        # find sentence end
        sid = words[i].get('sentence_id', 0)
        sentence_indices = []
        j = i
        while j < n and words[j].get('sentence_id', 0) == sid:
            sentence_indices.append(j)
            j += 1

        k = 0
        while k < len(sentence_indices):
            remaining = len(sentence_indices) - k
            group_size = min(max_words_per_group, remaining)
            if avoid_single_trailing_word and remaining == 1 and group_size == 1 and groups:
                # merge trailing single word into previous group if possible
                prev = groups[-1]
                if len(prev['words']) < max_words_per_group + 1:
                    prev['words'].append(words[sentence_indices[k]])
                    prev['end'] = words[sentence_indices[k]]['end']
                    k += 1
                    continue
            group_indices = sentence_indices[k:k + group_size]
            group_words = [words[idx] for idx in group_indices]
            groups.append({
                'group_id': group_id,
                'start': group_words[0]['start'],
                'end': group_words[-1]['end'],
                'words': group_words,
                'sentence_id': sid,
            })
            group_id += 1
            k += group_size

        i = j

    return groups


def align_corrected_words_with_map(original_words, corrected_text, sentence_gap_s=0.6):
    orig_tokens = [w['word'] for w in original_words]
    corr_tokens = tokenize(corrected_text)

    if not corr_tokens:
        corr_tokens = orig_tokens[:]

    ops = align_tokens_dp(orig_tokens, corr_tokens)
    corrected_tokens = force_same_length_tokens(orig_tokens, corr_tokens, ops)
    corrected_words = build_sentence_metadata(original_words, corrected_tokens, sentence_gap_s=sentence_gap_s)

    mapping = []
    for i, w in enumerate(corrected_words):
        orig = orig_tokens[i]
        corr = w['word']
        mapping.append({
            'index': i,
            'start': w['start'],
            'end': w['end'],
            'original_word': orig,
            'corrected_word': corr,
            'changed': orig != corr,
            'sentence_id': w['sentence_id'],
            'pause_before': w['pause_before'],
            'pause_after': w['pause_after'],
        })

    return corrected_words, mapping


def align_corrected_words(original_words, corrected_text, sentence_gap_s=0.6):
    corrected_words, _ = align_corrected_words_with_map(original_words, corrected_text, sentence_gap_s=sentence_gap_s)
    return corrected_words
