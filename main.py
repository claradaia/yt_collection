import conf
from aux import query_yes_no, discrepancy, export_csv, parse_niches
from googleapiclient.discovery import build
from datetime import datetime, timedelta
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
        country = item['snippet'].get('country', 'Not Available')
        channels[item['id']].extend([int(item['statistics']['subscriberCount']),
                                    item['statistics']['viewCount'],
                                    country])

    # format
    niche_rows = []
    for video in video_response['items']:
        row = [
            q,
            video['id'],
            video['snippet']['title'],
            datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d'),
            video['statistics']['viewCount']
        ]
        row.extend(channels[video['snippet']['channelId']])
        row.append(date_str)
        niche_rows.append(row)

    pprint(rows)

    # check discrepancy factor
    discrepants = discrepancy(niche_rows, 6)
    for index in discrepants:
        niche_rows[index][5] += '**'

    rows.extend(niche_rows)


# Generate final report
header = [
    'Niche',
    'Video URL',
    'Video Title',
    'Release Date',
    'Views Count',
    'Channel Title',
    'Channel Subscribers',
    'Channel Views',
    'Region Code',
    'Collection Date'
]

file_path = 'collection_result_' + date_str + '.csv'
export_csv(file_path, header, rows)
