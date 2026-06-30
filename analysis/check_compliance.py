import csv, json, os

AA = 'ACDEFGHIKLMNPQRSTVWY'

# Load R25 submission
with open(r'D:\workspace\round25\submission_r25.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

with open(r'D:\workspace\round25\final_6_r25.json', encoding='utf-8') as f:
    final6 = json.load(f)

# Load Exclusion List
excl = set()
excl_path = r'D:\生信\2026Protein Design\Exclusion_List.csv'
if os.path.exists(excl_path):
    with open(excl_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('Team') or line.startswith(','):
                continue
            parts = line.split(',')
            for p in parts:
                p = p.strip().upper()
                if len(p) > 50 and all(c in AA for c in p):
                    excl.add(p)

print(f'Exclusion list size: {len(excl)}')
print(f'R25 submission rows: {len(rows)}')
print()

all_pass = True
for i, (row, c) in enumerate(zip(rows, final6)):
    seq = row['Sequence'].strip()
    team = row['Team_Name'].strip()
    seq_id = row['Seq_ID'].strip()

    m_ok = seq[0] == 'M'
    len_ok = 220 <= len(seq) <= 250
    aa_ok = all(a in AA for a in seq)
    excl_ok = seq not in excl
    score = c.get('score', 0)

    ok = m_ok and len_ok and aa_ok and excl_ok
    if not ok:
        all_pass = False

    print(f'Seq {i+1}:')
    print(f'  Team_Name: {team}')
    print(f'  Seq_ID: {seq_id}')
    print(f'  Length: {len(seq)} (220-250: {"OK" if len_ok else "FAIL"})')
    print(f'  M start: {"OK" if m_ok else "FAIL"}')
    print(f'  Standard AA: {"OK" if aa_ok else "FAIL"}')
    print(f'  Not in Exclusion: {"OK" if excl_ok else "FAIL"}')
    print(f'  Score: {score:.4f}')
    print(f'  PASS: {"YES" if ok else "NO"}')
    print()

# Check CSV header
with open(r'D:\workspace\round25\submission_r25.csv', encoding='utf-8') as f:
    header = f.readline().strip()
expected_header = 'Team_Name,Seq_ID,Sequence'
header_ok = header == expected_header
print(f'CSV Header: "{header}"')
print(f'Header correct: {"OK" if header_ok else "FAIL"} (expected: "{expected_header}")')
print()
if not header_ok:
    all_pass = False
print(f'=== OVERALL: {"ALL PASS" if all_pass else "SOME FAILED"} ===')

# Also check if sequences are unique within submission
seqs = [r['Sequence'].strip() for r in rows]
if len(seqs) != len(set(seqs)):
    print('WARNING: Duplicate sequences in submission!')
    all_pass = False
else:
    print(f'All {len(seqs)} sequences are unique: OK')

# Check sfGFP reference for identity
sfgfp = 'MSKGEELFTGVVPILVELDGDVNGHKFSVRGEGEGDATNGKLTLKFICTTGKLPVPWPTLVTTLTYGVQCFSRYPDHMKRHDFFKSAMPEGYVQERTISFKDDGTYKTRAEVKFEGDTLVNRIELKGIDFKEDGNILGHKLEYNFNSHNVYITADKQKNGIKANFKIRHNIVEDGSVQLADHYQQNTPIGDGPVLLPDNHYLSTQSVLSKDPNEKRDHMVLLEFVTAAGITHGMDELYK'
print(f'\nsfGFP length: {len(sfgfp)}')
for i, s in enumerate(seqs):
    L = min(len(s), len(sfgfp))
    ident = sum(a == b for a, b in zip(s[:L], sfgfp[:L])) / L * 100
    print(f'  Seq {i+1} vs sfGFP identity: {ident:.1f}%')
