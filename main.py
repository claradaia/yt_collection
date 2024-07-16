import conf
from lib import query_yes_no, discrepancy, export_csv, parse_niches, export_html, export_pdf

from datetime import datetime, timedelta
from googleapiclient.discovery import build
from iso3166 import countries
from pytz import UTC
from pprint import pprint

# parse and check niches
niches = parse_niches(conf.NICHES_FILE)
if not query_yes_no(f"""{niches}\n\nDoes this look correct? [Y/n]:"""):
    exit(0)

# configure yt access
youtube = build('youtube', 'v3', developerKey=conf.API_KEY)

now = datetime.now(UTC)
date_str = now.strftime('%d-%m-%y')

# for csv
rows = []

for niche in niches:
    date_cutoff = datetime.isoformat(now - timedelta(days=niche['days']))
    q = niche['q']
    print(f'Searching niche \"{q}\" starting at {date_cutoff}...')

    search_response = youtube.search().list(
        part='snippet',
        q=q,
        type='video',
        publishedAfter=date_cutoff,
        order='viewCount',
        maxResults=10
    ).execute()
    n_videos = len(search_response['items'])
    print(f'Done. {n_videos} videos found.')

    video_ids = []
    channels = {}

    print(f'Gathering video details...')
    for item in search_response['items']:
        video_ids.append(item['id']['videoId'])
        channels[item['snippet']['channelId']] = [item['snippet']['channelTitle']]

    # Video stats
    video_response = youtube.videos().list(
        id=','.join(video_ids),
        part='snippet,statistics'
    ).execute()

    print(f'Done. Gathering channels details...')

    # Channel stats
    channel_response = youtube.channels().list(
        id=','.join(channels.keys()),
        part='snippet,statistics'
    ).execute()

    print(f'Done. Gathering...')
    for item in channel_response['items']:
        country_code = item['snippet'].get('country')
        country = countries.get(country_code).name if country_code else 'Not Available'
        channels[item['id']].extend([int(item['statistics']['subscriberCount']),
                                    item['statistics']['viewCount'],
                                    country])

    # organize for export
    niche_rows = []

    niche['videos'] = []
    niche['total_views_count'] = 0
    for video in video_response['items']:
        release_date = datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')

        # csv
        row = [
            q,
            video['id'],
            video['snippet']['title'],
            release_date,
            video['statistics']['viewCount']
        ]
        row.extend(channels[video['snippet']['channelId']])
        row.append(date_str)
        niche_rows.append(row)

        # html
        niche['total_views_count'] += int(video['statistics']['viewCount'])
        video_item = [
            video['id'],
            video['snippet']['title'],
            release_date,
            video['statistics']['viewCount'],
            channels[video['snippet']['channelId']][0],
            channels[video['snippet']['channelId']][1],
            channels[video['snippet']['channelId']][2],
            channels[video['snippet']['channelId']][3],
            False
        ]
        niche['videos'].append(video_item)

    pprint(rows)

    # check discrepancy factor
    discrepants = discrepancy(niche_rows, 6)
    for index in discrepants:
        niche_rows[index][5] += '**'
        niche['videos'][index][8] = True

    rows.extend(niche_rows)


# Generate report
header = [
    'Niche',
    'Video URL',
    'Video Title',
    'Release Date',
    'Views Count',
    'Channel Title',
    'Channel Subscribers',
    'Channel Views',
    'Country',
    'Collection Date'
]

result_filename = 'collection_result_' + date_str

export_csv(result_filename, header, rows)
export_html(result_filename, niches, date_str)
export_pdf(result_filename, niches, date_str)
