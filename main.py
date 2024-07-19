import conf
from lib import query_yes_no, discrepancy, export_csv, parse_niches, export_html, export_pdf, get_title_suggestions, \
    search_videos

from datetime import datetime, timedelta
from pytz import UTC

# parse and check niches
niches = parse_niches(conf.NICHES_FILE)
if not query_yes_no(f'{niches}\n\nDoes this look correct? [Y/n]:'):
    print(f'This is the value of conf.NICHES_FILE: {conf.NICHES_FILE}.\nCheck that the file name is correct and '
          'the contents of the file.')
    exit(0)

now = datetime.now(UTC)
date_str = now.strftime('%d-%m-%y')

# cap number of videos to be fetched to avoid exceeding YT API quota
max_pages_per_niche = int(conf.YT_DAILY_TOKENS / (len(niches) * 102))

for niche in niches:
    date_cutoff = datetime.isoformat(now - timedelta(days=niche['days']))
    q = niche['q']

    print(f'Searching \"{q}\" starting at {date_cutoff}...')
    niche['videos'] = search_videos(
        q=q,
        date_cutoff=date_cutoff,
        max_pages=max_pages_per_niche,
        max_videos=10
    )

    niche['total_views_count'] = 0
    for video in niche['videos']:
        niche['total_views_count'] += int(video['views'])

    print(f'Done. Detecting discrepancies...')
    # tag discrepancy factor
    discrepancy(niche['videos'])

    print(f'Done. Requesting title suggestions...')
    niche['titles'] = get_title_suggestions(q)

# Generate reports
result_filename = 'collection_result_' + date_str

export_csv(result_filename, niches, date_str)
export_html(result_filename, niches, date_str)
export_pdf(result_filename, niches, date_str)
