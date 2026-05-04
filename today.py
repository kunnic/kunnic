import datetime
from dateutil import relativedelta
import requests
import os
from lxml import etree
import time
import hashlib


# ==========================================
# 0. CẤU HÌNH
# ==========================================

HEADERS = {'authorization': 'token ' + os.environ['ACCESS_TOKEN']}
USER_NAME = 'kunnic'
BIRTHDAY = datetime.datetime(2003, 1, 1)  # ⚠️ ĐỔI ngày sinh thật của bạn vào đây
QUERY_COUNT = {
    'user_getter': 0, 'follower_getter': 0, 'graph_repos_stars': 0,
    'recursive_loc': 0, 'graph_commits': 0, 'loc_query': 0
}


# ==========================================
# 1. CÁC HÀM FETCH GITHUB API (từ code gốc của Andrew)
# ==========================================

def daily_readme(birthday):
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {} {}, {} {}{}'.format(
        diff.years, 'year' + format_plural(diff.years),
        diff.months, 'month' + format_plural(diff.months),
        diff.days, 'day' + format_plural(diff.days),
        ' 🎂' if (diff.months == 0 and diff.days == 0) else '')


def format_plural(unit):
    return 's' if unit != 1 else ''


def simple_request(func_name, query, variables):
    request = requests.post('https://api.github.com/graphql',
                            json={'query': query, 'variables': variables},
                            headers=HEADERS)
    if request.status_code == 200:
        return request
    raise Exception(func_name, ' has failed with a',
                    request.status_code, request.text, QUERY_COUNT)


def graph_repos_stars(count_type, owner_affiliation, cursor=None):
    query_count('graph_repos_stars')
    query = '''
    query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor, ownerAffiliations: $owner_affiliation) {
                totalCount
                edges { node { ... on Repository { nameWithOwner stargazers { totalCount } } } }
                pageInfo { endCursor hasNextPage }
            }
        }
    }'''
    variables = {'owner_affiliation': owner_affiliation, 'login': USER_NAME, 'cursor': cursor}
    request = simple_request(graph_repos_stars.__name__, query, variables)
    if count_type == 'repos':
        return request.json()['data']['user']['repositories']['totalCount']
    elif count_type == 'stars':
        return stars_counter(request.json()['data']['user']['repositories']['edges'])


def stars_counter(data):
    total = 0
    for node in data:
        total += node['node']['stargazers']['totalCount']
    return total


def recursive_loc(owner, repo_name, data, cache_comment,
                  addition_total=0, deletion_total=0, my_commits=0, cursor=None):
    query_count('recursive_loc')
    query = '''
    query ($repo_name: String!, $owner: String!, $cursor: String) {
        repository(name: $repo_name, owner: $owner) {
            defaultBranchRef { target { ... on Commit { history(first: 100, after: $cursor) {
                totalCount
                edges { node { ... on Commit { committedDate }
                    author { user { id } } deletions additions } }
                pageInfo { endCursor hasNextPage }
            } } } }
        }
    }'''
    variables = {'repo_name': repo_name, 'owner': owner, 'cursor': cursor}
    request = requests.post('https://api.github.com/graphql',
                            json={'query': query, 'variables': variables}, headers=HEADERS)
    if request.status_code == 200:
        if request.json()['data']['repository']['defaultBranchRef'] is not None:
            return loc_counter_one_repo(
                owner, repo_name, data, cache_comment,
                request.json()['data']['repository']['defaultBranchRef']['target']['history'],
                addition_total, deletion_total, my_commits)
        return 0
    force_close_file(data, cache_comment)
    if request.status_code == 403:
        raise Exception('Too many requests! Hit the anti-abuse limit.')
    raise Exception('recursive_loc() failed:', request.status_code, request.text)


def loc_counter_one_repo(owner, repo_name, data, cache_comment, history,
                         addition_total, deletion_total, my_commits):
    for node in history['edges']:
        if node['node']['author']['user'] == OWNER_ID:
            my_commits += 1
            addition_total += node['node']['additions']
            deletion_total += node['node']['deletions']
    if not history['edges'] or not history['pageInfo']['hasNextPage']:
        return addition_total, deletion_total, my_commits
    return recursive_loc(owner, repo_name, data, cache_comment,
                         addition_total, deletion_total, my_commits,
                         history['pageInfo']['endCursor'])


def loc_query(owner_affiliation, comment_size=0, force_cache=False, cursor=None, edges=None):
    if edges is None:
        edges = []
    query_count('loc_query')
    query = '''
    query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 60, after: $cursor, ownerAffiliations: $owner_affiliation) {
                edges { node { ... on Repository { nameWithOwner
                    defaultBranchRef { target { ... on Commit { history { totalCount } } } } } } }
                pageInfo { endCursor hasNextPage }
            }
        }
    }'''
    variables = {'owner_affiliation': owner_affiliation, 'login': USER_NAME, 'cursor': cursor}
    request = simple_request(loc_query.__name__, query, variables)
    if request.json()['data']['user']['repositories']['pageInfo']['hasNextPage']:
        edges += request.json()['data']['user']['repositories']['edges']
        return loc_query(owner_affiliation, comment_size, force_cache,
                         request.json()['data']['user']['repositories']['pageInfo']['endCursor'],
                         edges)
    return cache_builder(edges + request.json()['data']['user']['repositories']['edges'],
                         comment_size, force_cache)


def cache_builder(edges, comment_size, force_cache, loc_add=0, loc_del=0):
    cached = True
    os.makedirs('cache', exist_ok=True)
    filename = 'cache/' + hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest() + '.txt'
    try:
        with open(filename, 'r') as f:
            data = f.readlines()
    except FileNotFoundError:
        data = []
        if comment_size > 0:
            for _ in range(comment_size):
                data.append('This line is a comment block.\n')
        with open(filename, 'w') as f:
            f.writelines(data)

    if len(data) - comment_size != len(edges) or force_cache:
        cached = False
        flush_cache(edges, filename, comment_size)
        with open(filename, 'r') as f:
            data = f.readlines()

    cache_comment = data[:comment_size]
    data = data[comment_size:]
    for index in range(len(edges)):
        repo_hash, commit_count, *__ = data[index].split()
        if repo_hash == hashlib.sha256(edges[index]['node']['nameWithOwner'].encode('utf-8')).hexdigest():
            try:
                if int(commit_count) != edges[index]['node']['defaultBranchRef']['target']['history']['totalCount']:
                    owner, repo_name = edges[index]['node']['nameWithOwner'].split('/')
                    loc = recursive_loc(owner, repo_name, data, cache_comment)
                    data[index] = (repo_hash + ' '
                                   + str(edges[index]['node']['defaultBranchRef']['target']['history']['totalCount'])
                                   + ' ' + str(loc[2]) + ' ' + str(loc[0]) + ' ' + str(loc[1]) + '\n')
            except TypeError:
                data[index] = repo_hash + ' 0 0 0 0\n'

    with open(filename, 'w') as f:
        f.writelines(cache_comment)
        f.writelines(data)
    for line in data:
        loc = line.split()
        loc_add += int(loc[3])
        loc_del += int(loc[4])
    return [loc_add, loc_del, loc_add - loc_del, cached]


def flush_cache(edges, filename, comment_size):
    with open(filename, 'r') as f:
        data = []
        if comment_size > 0:
            data = f.readlines()[:comment_size]
    with open(filename, 'w') as f:
        f.writelines(data)
        for node in edges:
            f.write(hashlib.sha256(node['node']['nameWithOwner'].encode('utf-8')).hexdigest()
                    + ' 0 0 0 0\n')


def force_close_file(data, cache_comment):
    filename = 'cache/' + hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest() + '.txt'
    with open(filename, 'w') as f:
        f.writelines(cache_comment)
        f.writelines(data)


def commit_counter(comment_size):
    total_commits = 0
    filename = 'cache/' + hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest() + '.txt'
    with open(filename, 'r') as f:
        data = f.readlines()
    data = data[comment_size:]
    for line in data:
        total_commits += int(line.split()[2])
    return total_commits


def user_getter(username):
    query_count('user_getter')
    query = '''
    query($login: String!){
        user(login: $login) { id createdAt }
    }'''
    request = simple_request(user_getter.__name__, query, {'login': username})
    return ({'id': request.json()['data']['user']['id']},
            request.json()['data']['user']['createdAt'])


def follower_getter(username):
    query_count('follower_getter')
    query = '''
    query($login: String!){
        user(login: $login) { followers { totalCount } }
    }'''
    request = simple_request(follower_getter.__name__, query, {'login': username})
    return int(request.json()['data']['user']['followers']['totalCount'])


def query_count(funct_id):
    global QUERY_COUNT
    QUERY_COUNT[funct_id] += 1


# ==========================================
# 2. ASCII PORTRAIT + SVG OVERWRITE (code của bạn, đã sửa bug)
# ==========================================

def load_ascii_portrait(path="ascii_portrait.txt"):
    if not os.path.exists(path):
        print(f"Cảnh báo: Không tìm thấy file {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        rows = f.read().splitlines()
    if not rows:
        return []
    max_w = max(len(r) for r in rows)
    return [r.ljust(max_w) for r in rows]


def inject_ascii_portrait(root, rows, prefix="ascii_row_"):
    for el in root.iter():
        if not hasattr(el, 'get'):
            continue
        elem_id = el.get("id")
        if elem_id and elem_id.startswith(prefix):
            el.text = ""
    for i, row in enumerate(rows):
        elem_id = f"{prefix}{i:02d}"
        element = root.find(f".//*[@id='{elem_id}']")
        if element is not None:
            element.text = row


def justify_format(root, element_id, new_text, length=0):
    if isinstance(new_text, int):
        new_text = f"{new_text:,}"
    new_text = str(new_text)
    find_and_replace(root, element_id, new_text)
    just_len = max(0, length - len(new_text))
    if just_len <= 2:
        dot_string = {0: '', 1: ' ', 2: '. '}[just_len]
    else:
        dot_string = ' ' + ('.' * just_len) + ' '
    find_and_replace(root, f"{element_id}_dots", dot_string)


def find_and_replace(root, element_id, new_text):
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = new_text


def svg_overwrite(filename, age_data, commit_data, star_data, repo_data,
                  contrib_data, follower_data, loc_data, ascii_rows=None):
    tree = etree.parse(filename)
    root = tree.getroot()

    # === Stats từ GitHub API ===
    justify_format(root, 'commit_data',   commit_data,   22)
    justify_format(root, 'star_data',     star_data,     14)
    justify_format(root, 'repo_data',     repo_data,      6)
    justify_format(root, 'contrib_data',  contrib_data)
    justify_format(root, 'follower_data', follower_data, 10)
    justify_format(root, 'loc_data',      loc_data[2],    9)
    justify_format(root, 'loc_add',       loc_data[0])
    justify_format(root, 'loc_del',       loc_data[1],   7)

    # === Thông tin cá nhân tĩnh ===
    justify_format(root, 'age_data',         age_data,                          27)
    justify_format(root, 'os_data',          'Windows 11, Ubuntu 22.04',        24)
    justify_format(root, 'host_data',        'Ton Duc Thang University',        24)
    justify_format(root, 'kernel_data',      'Computer Science Student',        24)
    justify_format(root, 'ide_data',         'VS Code, PyCharm, Jupyter',       25)
    justify_format(root, 'lang_prog_data',   'Python, JavaScript, C++',         23)
    justify_format(root, 'lang_spoken_data', 'Vietnamese, English',             19)
    justify_format(root, 'research_data',    'CV, ML, Sentiment Analysis',      26)
    justify_format(root, 'hobbies_data',     'Reading, Psychology, Coding',     27)
    justify_format(root, 'email_data',       'official.nguyenduchuy@gmail.com', 31)
    justify_format(root, 'github_data',      '@kunnic',                          7)

    if ascii_rows:
        inject_ascii_portrait(root, ascii_rows)

    tree.write(filename, encoding='utf-8', xml_declaration=True)


# ==========================================
# 3. KHỐI THỰC THI CHÍNH
# ==========================================

if __name__ == "__main__":
    print("Bắt đầu cập nhật Neofetch cho GitHub Profile...")

    # 1. Lấy User ID + ngày tạo account
    print("→ Đang fetch user data...")
    user_data, acc_date = user_getter(USER_NAME)
    OWNER_ID = user_data

    # 2. Tính tuổi (uptime)
    age_data = daily_readme(BIRTHDAY)

    # 3. Đếm Lines of Code (cache lần đầu sẽ chậm, các lần sau nhanh)
    print("→ Đang đếm Lines of Code (lần đầu có thể mất vài phút)...")
    total_loc = loc_query(['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'], 7)

    # 4. Đếm commits từ cache đã build ở bước trên
    commit_data = commit_counter(7)

    # 5. Stars, Repos, Contributions, Followers
    print("→ Đang fetch stars/repos/contribs/followers...")
    star_data     = graph_repos_stars('stars', ['OWNER'])
    repo_data     = graph_repos_stars('repos', ['OWNER'])
    contrib_data  = graph_repos_stars('repos', ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'])
    follower_data = follower_getter(USER_NAME)

    # 6. Format LOC: thêm dấu phẩy ngàn
    for i in range(len(total_loc) - 1):
        total_loc[i] = '{:,}'.format(total_loc[i])

    # 7. Đọc ASCII portrait
    print("→ Đang tải ascii_portrait.txt...")
    ascii_rows = load_ascii_portrait("ascii_portrait.txt")

    # 8. Ghi đè cả 2 SVG
    for svg_file in ['dark_mode.svg', 'light_mode.svg']:
        if os.path.exists(svg_file):
            print(f"→ Đang cập nhật {svg_file}...")
            svg_overwrite(svg_file, age_data, commit_data, star_data, repo_data,
                          contrib_data, follower_data, total_loc[:-1], ascii_rows)
        else:
            print(f"⚠ Không tìm thấy {svg_file}")

    print(f"\n✓ Hoàn tất! Tổng số API calls: {sum(QUERY_COUNT.values())}")