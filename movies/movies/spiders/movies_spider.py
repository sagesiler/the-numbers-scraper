from pathlib import Path
import scrapy

#links:
#https://www.the-numbers.com/box-office-records/worldwide/all-movies/production-methods/digital-animation
#https://www.the-numbers.com/box-office-records/worldwide/all-movies/production-methods/hand-animation
#https://www.the-numbers.com/box-office-records/worldwide/all-movies/production-methods/stop-motion-animation
#https://www.the-numbers.com/box-office-records/worldwide/all-movies/production-methods/rotoscoping

#scrape into csv file

class MoviesSpider(scrapy.Spider):
    name = "movies"

    def start_requests(self):
        urls = [
            "https://www.the-numbers.com/box-office-records/worldwide/all-movies/production-methods/digital-animation",
            "https://www.the-numbers.com/box-office-records/worldwide/all-movies/production-methods/hand-animation",
            "https://www.the-numbers.com/box-office-records/worldwide/all-movies/production-methods/stop-motion-animation",
            "https://www.the-numbers.com/box-office-records/worldwide/all-movies/production-methods/rotoscoping"
        ]
        for i in range(1, 18): #add the rest of the digital animation pages
            link = ("https://www.the-numbers.com/box-office-records/worldwide/all-movies/production-methods/digital-animation/" +
                    str(i) + "01")
            urls.append(link)
        for i in range(1, 3): #add the rest of the hand animation pages
            link = ("https://www.the-numbers.com/box-office-records/worldwide/all-movies/production-methods/hand-animation/" +
                    str(i) + "01")
            urls.append(link)

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_movies)

    def parse_movies(self, response): #gets urls correctly
        for link in response.css('table tr a::attr(href)'):
            if link.get().startswith("/movie"):
                href = link.get()
                url = "https://www.the-numbers.com" + href
                yield scrapy.Request(url=url, callback=self.get_attributes)

    def get_attributes(self, response):
        title = response.css('h1::text').get() #attribute 1

        year = title.split(' ') #attribute 2
        year = year[len(year) - 1] #the year is always the last part of title, separated by a space
        year = year[1:5] #since length will always be 6, this just removes parentheses

        domestic = response.css('table#movie_finances td::text')[0].get() #attribute 3
        if domestic == 'n/a':
            domestic = 0
        else:
            try: #in scenarios where gross isn't high enough
                domestic = domestic.replace('$', '')
                domestic = domestic.replace(',', '')
            except AttributeError:
                pass
            domestic = int(domestic)

        try: #since not all pages have an international section
            international = response.css('table#movie_finances td::text')[1].get() #attribute 4
        except IndexError:
            international = 0
        if international == 'n/a':
            international = 0
        else:
            try:
                international = international.replace('$', '')
                international = international.replace(',', '')
            except AttributeError:
                pass
            international = int(international)

        try: #since not all pages have a worldwide section
            worldwide = response.css('table#movie_finances td::text')[2].get() #attribute 5
        except IndexError:
            worldwide = domestic #since this should only happen if there's no international value
        if worldwide == 'n/a': #shouldn't happen but just in case
            worldwide = domestic
        else:
            try:
                worldwide = worldwide.replace('$', '')
                worldwide = worldwide.replace(',', '')
            except AttributeError:
                pass
            worldwide = int(worldwide)
        
        rating = "NR" #attribute 6; initially set to a default since not all movies have one
        franchise = "None" #attribute 7; initially set to a default since not all movies have one
        genre = "N/A" #attribute 8; initially set in case one is not listed
        animation = "N/A" #attribute 9; initiallly set in case one is not listed
        creative = "N/A" #attribute 10; initially set in case one is not listed
        distributor = "N/A" #attribute 11; initially set in case one is not listed
        language = "N/A" #attribute 12; initially set in case one is not listed
        for stat in response.css('table td a'):
            if stat.css('::attr(href)').get().startswith("/market/mpaa-rating"): #change rating if applicable
                rating = stat.css('::text').get()
                if rating == "Not Rated": #for consistency
                    rating = "NR"
            if stat.css('::attr(href)').get().startswith("/movies/franchise"): #add franchise if applicable
                franchise = stat.css('::text').get()
            if stat.css('::attr(href)').get().startswith("/market/genre"): #get genre
                genre = stat.css('::text').get()
            if stat.css('::attr(href)').get().startswith("/market/production-method"):  #get animation type
                animation = stat.css('::text').get()
            if stat.css('::attr(href)').get().startswith("/market/creative-type"):  #get creative type
                creative = stat.css('::text').get()
            if (stat.css('::attr(href)').get().startswith("/market/distributor")
                    and (distributor == "N/A")): #get first domestic theater distributor, ignore rereleases
                distributor = stat.css('::text').get()
            if stat.css('::attr(href)').get().startswith("/language"): #get original language(s) of movie
                language = stat.css('::text').get()

        moviedict = {"Title": title, "Release Year": year, "Domestic Gross": domestic,
                "International Gross": international, "Worldwide Gross": worldwide,
                "Rating": rating, "Franchise": franchise, "Genre": genre,
                "Animation Type": animation, "Creative Type": creative,
                "Distributor": distributor, "Languages": language}
        yield moviedict
