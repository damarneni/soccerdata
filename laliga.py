import requests, codecs
from bs4 import BeautifulSoup

def write_laliga_csv(outfile, results):
    outfile.write("home, homescore, awayscore, away, date, group\n")
    for result in results:
        outfile.write(u'{0}, {1}, {2}, {3}, "{4}", "{5}"\n'.format(*result))

def parse_laliga_page(soup):
    days = soup.find_all("table", "tablehead")
    results = []
    for day in days:
        date = day.tr.text
        for game in day.find_all("tr")[2:]:
            cells = game.find_all("td")

            status = cells[0].text
            #skip in-progress games
            if "FT" not in status: continue

            home = cells[1].text
            result = cells[2].text
            away = cells[3].text
            group = cells[4].text

            try:
                homescore, awayscore = result.split("-")
            except ValueError:
                print "unable to parse game {0}".format(cells)
                continue

            results.append((home, homescore, awayscore, away, date, group))

    return results

def get(url, retries=10):
    #TODO: backoff
    r = requests.get(url)
    for _ in range(retries):
        if r.status_code == 200:
            return r
        print "retrying"
        r = requests.get(url)
    raise Exception("GET failed.\nstatus: {0}\nurl: {1}".format(r.status_code, url))

def laliga():
    url = "http://espnfc.com/results/_/league/esp.1/spanish-la-liga?cc=5901"
    url = "http://espnfc.com/results/_/league/esp.1/date/20070617/spanish-la-liga"

    print "getting %s" % url
    r = get(url)

    soup = BeautifulSoup(r.text)
    season = soup.h2.text.split(" ")[0]
    results = parse_laliga_page(soup)

    while 1:
        previous = soup.find("p", "prev-next-links").a
        if not "Previous" in previous.text: break
        url = previous["href"]

        print "getting %s" % url
        r = get(url)

        soup = BeautifulSoup(r.text)
        if soup.h2.text.split(" ")[0] != season:
            #uncomment all this to download previous seasons' data
            season_f = "{0}_{1}".format(season[2:4], season[5:7])
            out = codecs.open("data/laliga_{0}.csv".format(season_f), 'w', "utf8")
            write_laliga_csv(out, results)

            season = soup.h2.text.split(" ")[0]
            print "found season: {0}".format(season)
            results = []

        results += parse_laliga_page(soup)

    season_f = "{0}_{1}".format(season[2:4], season[5:7])
    out = codecs.open("data/laliga_{0}.csv".format(season_f), 'w', "utf8")
    write_laliga_csv(out, results)

if __name__=="__main__":
    laliga()
