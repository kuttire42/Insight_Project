#!/usr/bin/env python3

# requires: selenium, chromium-driver, retry

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import selenium.common.exceptions as sel_ex
import sys
import time
import urllib.parse
from retry import retry
import argparse
import logging
import os
import io
import requests
from PIL import Image
import hashlib

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger()
retry_logger = None

css_thumbnail = "img.Q4LuWd"
css_large = "img.n3VNCb"
css_load_more = ".mye4qd"
selenium_exceptions = (sel_ex.ElementClickInterceptedException, sel_ex.ElementNotInteractableException, sel_ex.StaleElementReferenceException)

def scroll_to_end(wd):
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")

@retry(exceptions=KeyError, tries=6, delay=0.1, backoff=2, logger=retry_logger)
def get_thumbnails(wd, want_more_than=0):
    wd.execute_script("document.querySelector('{}').click();".format(css_load_more))
    thumbnails = wd.find_elements_by_css_selector(css_thumbnail)
    n_results = len(thumbnails)
    if n_results <= want_more_than:
        raise KeyError("no new thumbnails")
    return thumbnails

@retry(exceptions=KeyError, tries=6, delay=0.1, backoff=2, logger=retry_logger)
def get_image_src(wd):
    actual_images = wd.find_elements_by_css_selector(css_large)
    sources = []
    for img in actual_images:
        src = img.get_attribute("src")
        if src.startswith("http") and not src.startswith("https://encrypted-tbn0.gstatic.com/"):
            sources.append(src)
    if not len(sources):
        raise KeyError("no large image")
    return sources

@retry(exceptions=selenium_exceptions, tries=6, delay=0.1, backoff=2, logger=retry_logger)
def retry_click(el):
    el.click()

def get_images(wd, start=0, n=20, out=None):
    thumbnails = []
    count = len(thumbnails)
    while count < n:
        print(count)
        scroll_to_end(wd)
        try:
            thumbnails = get_thumbnails(wd, want_more_than=count)
        except KeyError as e:
            logger.warning("cannot load enough thumbnails")
            break
        count = len(thumbnails)
    sources = []
    for tn in thumbnails:
        try:
            retry_click(tn)
        except selenium_exceptions as e:
            logger.warning("main image click failed")
            continue
        sources1 = []
        try:
            sources1 = get_image_src(wd)
        except KeyError as e:
            pass
            # logger.warning("main image not found")
        if not sources1:
            tn_src = tn.get_attribute("src")
            if not tn_src.startswith("data"):
                logger.warning("no src found for main image, using thumbnail")
                sources1 = [tn_src]
            else:
                logger.warning("no src found for main image, thumbnail is a data URL")
        for src in sources1:
            if not src in sources:
                sources.append(src)
                if out:
                    print(src, file=out)
                    out.flush()
        if len(sources) >= n:
            break
    return sources

def google_image_search(wd, query, safe="off", n=20, opts='', out=None):
    search_url_t = "https://www.google.com/search?safe={safe}&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img&tbs={opts}"
    search_url = search_url_t.format(q=urllib.parse.quote(query), opts=urllib.parse.quote(opts), safe=safe)
    print(search_url)
    wd.get(search_url)
    sources = get_images(wd, n=n, out=out)
    return sources

def persist_image(folder_path:str,url:str):
    try:
        image_content = requests.get(url).content
    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        image_file = io.BytesIO(image_content)
        image = Image.open(image_file).convert('RGB')
        file_path = os.path.join(folder_path, hashlib.sha1(image_content).hexdigest()[:10] + '.jpg')
        with open(file_path, 'wb') as f:
            image.save(f, "JPEG", quality=100, subsampling=0)
        print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as e:
        print(f"ERROR - Could not save {url} - {e}")

def main():
    parser = argparse.ArgumentParser(description='Fetch image URLs from Google Image Search.')
    parser.add_argument('--safe', type=str, default="off", help='safe search [off|active|images]')
    parser.add_argument('--opts', type=str, default="", help='search options, e.g. isz:lt,islt:svga,itp:photo,ic:color,ift:jpg')
    #parser.add_argument('query', type=str, help='image search query')
    #parser.add_argument('n', type=int, default=20, help='number of images (approx)')
    search_term = "rambler ranch home"
    number_of_images = 10
    target_path = './images'
    args = parser.parse_args()

    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    starting_time = time.time()
    with webdriver.Chrome(options=opts) as wd:
        sources = google_image_search(wd, search_term, safe=args.safe, n=number_of_images, opts=args.opts, out=sys.stdout)
        #sources = google_image_search(wd, args.query, safe=args.safe, n=args.n, opts=args.opts, out=sys.stdout)

    print("Downloading images from URLs")
    target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' ')))
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    for elem in sources:
        print(elem)
        persist_image(target_folder, elem)

    print("--- %s seconds ---" % (time.time() - starting_time))
main()

"""
https://www.oldhouseonline.com/.image/ar_1:1%2Cc_fill%2Ccs_srgb%2Cfl_progressive%2Cq_auto:good%2Cw_1200/MTUyMDI5ODQ0NTU1NzA0MjAy/1-tudor-ohi.jpg
https://architecturestyles.files.wordpress.com/2011/10/copy-of-img_6003.jpg
https://hgtvhome.sndimg.com/content/dam/images/hgtv/fullset/2013/2/19/4/DesignLens_large-tudor-home_s4x3.jpg.rend.hgtvcom.1280.960.suffix/1400976380192.jpeg
WARNING:root:no src found for main image, thumbnail is a data URL
https://isarchitecture.com/site/wp-content/uploads/teague-historic-tudor-addition-01.jpg
https://ca-times.brightspotcdn.com/dims4/default/4fbb40b/2147483647/strip/true/crop/2000x1124+0+0/resize/840x472!/quality/90/?url=https%3A%2F%2Fcalifornia-times-brightspot.s3.amazonaws.com%2F3f%2Fe1%2Fba3a45d6958f0684d226c3482aac%2Fla-1515809160-hhiee0co6i-snap-image
https://i.pinimg.com/originals/c1/3c/bd/c13cbddbdd52d1c0b46eeacbac5fcdb0.jpg
https://lh3.googleusercontent.com/proxy/AX_57klb6nKpRXqhpk8mV3t7qlOTwDethPOY2B9zLbuSaCRoP21nbl00fZQ6O3PNJOXMiUh8XXhYhAICGuBgCbu0L6A5q598IJLpsUt0Z3wtKO81D35AXm3mXWe3aGuGHc6jSnEXtN3g6pkw1_Avo5zRfSQNrTQOGmS2umRbjuHQZ0L9EtpgUYQ
https://live.staticflickr.com/7905/46466133792_2cb0c2dd19_b.jpg
https://study.com/cimages/multimages/16/800px-rowe_house_wayland_ny_apr_11.jpg
https://historiclouisville.com/wp-content/uploads/2016/11/tudor-1.jpg
https://www.buffaloah.com/a/archsty/tud/tc.jpg
https://www.priceypads.com/wp-content/uploads/2019/07/065df77beffe0e45a33e83277672853c8b049a11_original-1.jpg
WARNING:root:no src found for main image, thumbnail is a data URL
WARNING:root:no src found for main image, thumbnail is a data URL
https://www.phillymag.com/wp-content/uploads/sites/3/2020/03/house-for-sale-east-falls-tudor-revival-exterior-front-brightmls.jpg
https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Ascott_House.jpg/300px-Ascott_House.jpg
https://www.phillymag.com/wp-content/uploads/sites/3/2019/12/house-for-sale-gladwyne-young-tudor-exterior-front-brightmls.png
https://architecturestyles.files.wordpress.com/2011/10/copy-of-p1010088.jpg
https://sites.google.com/site/buildingwatching/_/rsrc/1468872724403/styles/21-the-tudor/21a.%20Tudor%20%28Kitchener%29__small.jpg?height=300&width=400
https://s3-production.bobvila.com/articles/wp-content/uploads/2018/11/Tudor_Houses.jpg
https://wps-static-williampittsothe.netdna-ssl.com/wp-content/uploads/2015/06/TudorRevival-.jpg
https://www.finehomebuilding.com/app/uploads/2018/07/Tudor-Revival_Front-Elevation-After-mainjpg
https://i.pinimg.com/originals/3e/3f/94/3e3f94664f8e96911b0215b6f27adea6.jpg
https://cdn.homedit.com/wp-content/uploads/2018/05/Tudor-revival-wood-shutters.jpg
https://architecturestyles.files.wordpress.com/2011/10/copy-of-p6220181.jpg
https://c8.alamy.com/comp/EA9E3W/tudor-revival-house-jamaica-estates-queens-new-york-EA9E3W.jpg
https://media.mlive.com/kzgazette/features_impact/photo/tudor-homejpg-40484565872e47bc.jpg
https://tba.nyc3.digitaloceanspaces.com/wordpress/christopherai.com/wp-content/uploads/2018/11/Tudor-Revival-Cottage-Christopher-Architecture-and-Interiors-1024x604.jpg
https://lh3.googleusercontent.com/proxy/FsoYfgpJO6b9PoSmtUWiDXXo8qkM1sBDfOGXpjf5RNxNdghrYsfO6vfOQPThZZV2W08xNd_8fDDXkoYUap4fQjzw_6Xzc81ydTjOw2jayMMlWNDCmtwtrIIlhrB2lf6njqE7kxvzPFnykTi4k32q
https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/%281%29Old_English_style_house_Killara-1.jpg/220px-%281%29Old_English_style_house_Killara-1.jpg
https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Builder%27s_tudorbethan.jpg/220px-Builder%27s_tudorbethan.jpg
https://lh3.googleusercontent.com/proxy/7U3MDoxLEpxJfcK0PbaLxnGRpT9bShb5D5rJR62ELz_LDSi_xGAyXUW9f5TFKejMt3E94FQgV3wGYjfQKKwgp8e0HWNsiNatzXAuL1bjPtufac95bpXFZOa55i7I6TSQxOSdqkYzd1WEbb1biHlHQiAzENW_vLKhiWpN9BPB_BZ-o-v1Dx4Y5jtystL_rpyHx2I
https://www.priceypads.com/wp-content/uploads/2020/02/011PrintSize-1-2.jpg
https://cdn.vox-cdn.com/thumbor/60DPrNK8d7bvqjZv_JYQd7ioXjg=/0x0:3980x2983/1200x800/filters:focal(1336x1370:1972x2006)/cdn.vox-cdn.com/uploads/chorus_image/image/66588508/905_Berkshire_Ext__1_.0.jpg
https://bloximages.newyork1.vip.townnews.com/lancasteronline.com/content/tncms/assets/v3/editorial/2/b2/2b282b3c-f631-5953-97aa-c0086bf57213/5230c97db14a1.image.jpg
https://upload.wikimedia.org/wikipedia/commons/thumb/5/54/Beaney_Institute_002.jpg/170px-Beaney_Institute_002.jpg
https://bloximages.chicago2.vip.townnews.com/insidenova.com/content/tncms/assets/v3/editorial/0/c7/0c7ff104-f643-11e8-b46f-7bae5b57d89a/5c03f3c6cd7a2.image.jpg?resize=1200%2C790
https://cdn.captivatinghouses.com/wp-content/uploads/2020/02/IMG_3836.jpg
https://nessmagazine.com/wp-content/uploads/2019/09/01_FEATURE_40118-Rearfacade-1600x1070.jpg
https://cdn.captivatinghouses.com/wp-content/uploads/2019/02/IMG_9730.jpg
https://architecturestyles.files.wordpress.com/2011/10/copy-of-p5290044.jpg
https://images.squarespace-cdn.com/content/v1/54c04510e4b07d778fe3cd1a/1558561492623-6RQ4G13JR26X988LITWU/ke17ZwdGBToddI8pDm48kAt72yGFwHZjoxtmj75n0VMUqsxRUqqbr1mOJYKfIPR7LoDQ9mXPOjoJoqy81S2I8N_N4V1vUb5AoIIIbLZhVYy7Mythp_T-mtop-vrsUOmeInPi9iDjx9w8K4ZfjXt2dvp1wM0jvciobd5mvjBb-PkjbbxSYDSdt-BIyUswy_5eG6v6ULRah83RgHXAWD5lbQ/sold-by-salgado_francisco-salgado_realtor_real-estate-broker-portland-tudor-revival-homes-for-sale_0181.jpg?format=2500w
https://hips.hearstapps.com/clv.h-cdn.co/assets/16/36/980x653/gallery-1473187437-country-listing-tudor-tennessee-1016.jpg?resize=480:*
https://ca-times.brightspotcdn.com/dims4/default/2bc1043/2147483647/strip/true/crop/2048x959+0+0/resize/840x393!/quality/90/?url=https%3A%2F%2Fcalifornia-times-brightspot.s3.amazonaws.com%2F09%2F1d%2F33d3eaf8caab6d9f0fb22a9c5e54%2Fla-fi-hotprop-tudor-mansion-barker-20181115-ph-013
https://www.thevintagenews.com/wp-content/uploads/2019/02/ecqubple.jpg
https://www.antiquehomesmagazine.com/wp-content/uploads/2017/09/Antique-Homes-Magazine-Tudor-Revival-3-994x1024.jpg
https://images.trvl-media.com/hotels/33000000/32430000/32420100/32420059/278c2a37_z.jpg
https://images.squarespace-cdn.com/content/v1/54c04510e4b07d778fe3cd1a/1557791948996-M91Q6ENO4OV92IC2RZVS/ke17ZwdGBToddI8pDm48kFWxnDtCdRm2WA9rXcwtIYR7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QPOohDIaIeljMHgDF5CVlOqpeNLcJ80NK65_fV7S1UcTSrQkGwCGRqSxozz07hWZrYGYYH8sg4qn8Lpf9k1pYMHPsat2_S1jaQY3SwdyaXg/sold-by-salgado_francisco-salgado_realtor_real-estate-broker_portland-tudor-homes-for-sale6321.jpg
https://luxport.s3.amazonaws.com/137732/98F40186-FB95-45D1-A5F8-AA7F140F1D48%2BAA7F140F1D48_001_H.jpg
https://www.phillymag.com/wp-content/uploads/sites/3/2019/04/house-for-sale-chestnut-hill-tudor-revival-exterior-front-sivel-group.jpg
https://st.hzcdn.com/fimgs/0c52618a067bfa15_5531-w500-h379-b0-p0--.jpg
https://luxesource.com/wp-content/uploads/2019/07/LX_PNW45_HOM_North-Forest-18.jpg
https://cdn.vox-cdn.com/thumbor/7BRlGnVUpADQwerrvNELnoIVGMM=/0x0:2500x1667/1200x800/filters:focal(1046x438:1446x838)/cdn.vox-cdn.com/uploads/chorus_image/image/65567984/1.0.jpg
https://www.priceypads.com/wp-content/uploads/2020/03/e8df1b0a8bc0c728f00ce8cb10c90e04l-m3520956084xd-w1020_h770_q80.jpg
https://www.windermere.com/uploads/architectural_styles/15/large_front_TudorRevival.jpg
https://cdn.captivatinghouses.com/wp-content/uploads/2019/09/IMG_4473.jpg
https://www.oldhousedreams.com/wp-content/uploads/2019/04/1-4thehillsohd.jpg
https://h2realestate.com/wp-content/uploads/2016/09/tudorrevival.jpg
https://i.pinimg.com/originals/b8/99/45/b899451b05f95613918a3822f04fde78.jpg
https://mainehomes.com/wp-content/uploads/2017/09/1.jpg
WARNING:root:no src found for main image, using thumbnail
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcR3Mjxl65Hr36t9vtJymVnMRQ3f5gMMKm2t98gllNaJCeMuN6xy&usqp=CAU
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcQgA0eaNdEBjXwAmfg5FMdN4EFpWQDmihtdGXPStJHUDXJF4qWr&usqp=CAU
WARNING:root:no src found for main image, using thumbnail
https://study.com/cimages/multimages/16/320px-1052-seminole-detroit-michigan-henry-leland.jpg
https://media.mlive.com/kzgazette/features_impact/photo/tudor-home-2jpg-cc18082dd729c8f6.jpg
https://bluestoneconstruction.com/wp-content/uploads/2018/08/5b62fab7624b34526030fa6d_Bluestone-Construction_Biltmore_2_exterior.jpg
https://i.pinimg.com/originals/f7/09/56/f70956ad5b8fe196260365db6a2df1ef.jpg
https://www.urbanaillinois.us/sites/default/files/images/PENNSYLVANIA_W_806_3B.jpg
https://cdn.vox-cdn.com/thumbor/BXPmw6nwik4MomfBIvWea87Ur3I=/0x0:4200x2800/1200x800/filters:focal(1764x1064:2436x1736)/cdn.vox-cdn.com/uploads/chorus_image/image/63894610/2016_W_Boston_Blvd_Detroit_MI_print_002_11_2016_West_Boston_Boulevard_4200x2800_300dpi.0.jpg
https://c8.alamy.com/comp/EA9E3P/tudor-revival-house-forest-hills-gardens-queens-new-york-EA9E3P.jpg
https://d3exkutavo4sli.cloudfront.net/wp-content/uploads/2020/03/mls-photo.jpg
https://artsandcraftshomes.com/.image/t_share/MTQ0NDY2MzAxNjU0NDExMTYz/2-2.jpg
https://blog.pacificunion.com/wp-content/uploads/tudorsocal.jpg
https://i.pinimg.com/600x315/cb/d1/bf/cbd1bff2f51be2f41ecef9cf4fe8cef6.jpg
https://architecturestyles.files.wordpress.com/2011/10/copy-of-p1010199.jpg
https://i2.wp.com/www.gardenstogables.com/wp-content/uploads/2020/01/irvine.jpg
https://www.oldhouseonline.com/.image/ar_16:9%2Cc_fill%2Ccs_srgb%2Cfl_progressive%2Cg_faces:center%2Cq_auto:good%2Cw_768/MTUyMDI5ODY4NzE0ODk0ODMw/int-ac-wdwk-073niedfm04.jpg
https://vanderhornarchitects.com/wp-content/uploads/2017/11/english-tudor-revival-01-1024x600.jpg
https://img.particlenews.com/image.php?type=thumbnail_1024x576&url=4BvyAu_0NqCf0RC00
https://luxport.s3.amazonaws.com/1634/8B90F860-6D87-4491-9CF4-1170DBE5CD19%2B1170DBE5CD19_001_H.jpg
https://static.planetminecraft.com/files/resource_media/screenshot/1522/tudor-exterior018966524.jpg
https://luxesource.com/wp-content/uploads/2019/08/TudorRevivedCHICOVER-1024x683.jpg
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcS5f8UUBH6BTrX21t4FrqYTZsf5J1R58Kgb8FMTmCEE5DJsr35O&usqp=CAU
WARNING:root:no src found for main image, using thumbnail
https://s.hdnux.com/photos/71/47/25/15103326/3/rawImage.jpg
https://lh3.googleusercontent.com/proxy/gFReE2B2QBUC5PN2GSky1510exlSEzqq7IcDH1NVMJbOoERrC_k0xs0WpUySbuCjyLWXhBDtwdifwq11x3-voZ2x794CMcgQ2wYxcNPOtRm4J7fnhtWGh5uH9fm5j89UcpYJbff_pDWBNVLPmKGfDBUsITieCCaJmWucVSzxYEIiqdgq4oc
https://i.pinimg.com/originals/4c/c5/6d/4cc56ded5ee4c131671d0de401faa832.png
https://cdn.captivatinghouses.com/wp-content/uploads/2020/02/IMG_3908.jpg
https://www.oldhousedreams.com/wp-content/uploads/2014/03/1-2805Harrison.jpg
https://thumbs.dreamstime.com/b/tudor-revival-architecture-san-francisco-usa-april-style-residential-houses-russian-hill-140145835.jpg
https://www.oldhouseonline.com/.image/t_share/MTcxMjI4MTExMzQwMzE2MzM5/ext-20191029_ohj_rwhc_003_s.jpg
https://chaffeybuildinggroup.com/wp-content/uploads/2018/06/The-Tutor-Revival.jpg
https://bungalower.com/wp-content/uploads/2018/10/jasmin1.jpg
WARNING:root:no src found for main image, using thumbnail
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcTU9mNf6iu2P3eEKlK4TWVPjyGyDmxX8_FTEiCd0IDPoFURrTy0&usqp=CAU
https://c8.alamy.com/comp/EA9E4D/tudor-revival-house-jamaica-estates-queens-new-york-EA9E4D.jpg
https://www.stlouis.style/wp-content/uploads/2019/01/unspecified-2-940x590.jpeg
https://images.squarespace-cdn.com/content/v1/5b57849e31d4df313991bf08/1534436693357-3YEOLS121CGOPVHVVXEL/ke17ZwdGBToddI8pDm48kBjf5nluv80n1InqWsEyWeV7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QPOohDIaIeljMHgDF5CVlOqpeNLcJ80NK65_fV7S1UQU21_LU8mfjOzCRFei9_jy-MuOofCuoaEtM5pu3XAQ4Dzq2EZWpnixARrMWsOOAVw/006_tudor_revival.jpg
https://cdn.vox-cdn.com/thumbor/X3fTosu-RyvTA5LM8HbidwrJBkU=/1400x1400/filters:format(jpeg)/cdn.vox-cdn.com/uploads/chorus_asset/file/19355871/Photo_Apr_02__12_26_41_PM__1_.jpg
https://cdn.homedit.com/wp-content/uploads/2018/05/Tudor-revival-bright-red-door.jpg
https://www.thelakotagroup.com/wp-content/uploads/2013/03/tudor-revival-house-at-519-edgewood-place.jpeg
https://i.pinimg.com/originals/db/85/2e/db852e0e86b63f5156c8989fb57bd10e.jpg
https://images.squarespace-cdn.com/content/v1/5b57849e31d4df313991bf08/1534436693358-WSC0LMPQNVC3HOAA5GIB/ke17ZwdGBToddI8pDm48kLCpfTarCW85PNATIQfmTB57gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QPOohDIaIeljMHgDF5CVlOqpeNLcJ80NK65_fV7S1UT8h568yjhWvv1FJ5Mh4XOAfxV19IBS7YUu6H9TAlQ2i5mK74YqutHtu4hBeWE_-Pw/007_tudor_revival.jpg
https://i0.wp.com/www.gardenstogables.com/wp-content/uploads/2020/01/Fullscreen-capture-1142020-71804-PM.jpg
https://img.particlenews.com/image.php?type=thumbnail_1024x576&url=3FmZAV_0NjLWZSn00
WARNING:root:no src found for main image, using thumbnail
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcR-7Wm_iUJeVhG27TodyZRlsxAtdQbVKj8DYEAjH--0eIfUxb7l&usqp=CAU
https://www.priceypads.com/wp-content/uploads/2019/10/1659505-33.jpg
https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Saitta_House_Dyker_Heights.JPG/220px-Saitta_House_Dyker_Heights.JPG
https://i.redd.it/3eb5vyuyhln01.jpg
https://www.brownstoner.com/wp-content/uploads/2020/01/tuxedo-park-116-tower-hill-road-william-mitchell-vail-hoffman-paxhurst-exterior.jpg
https://www.capecodtimes.com/storyimage/CC/20191206/NEWS/191209700/AR/0/AR-191209700.jpg
https://www.oldhousedreams.com/wp-content/uploads/2019/04/1-2481Charney.jpg
https://cdn.captivatinghouses.com/wp-content/uploads/2020/05/IMG_8881.jpg
https://www.indianalandmarks.org/wp-content/uploads/2019/08/HHS-Tudor-Rev-N-Meridian-HD-Indpls.jpg
https://si.wsj.net/public/resources/images/OB-TS347_TudorR_H_20120711121830.jpg
https://www.wentworthstudio.com/wp-content/uploads/2017/01/tudor-home-2-crop.png
https://circaoldhouses.com/wp-content/uploads/2019/10/jawdropper-tudor1.jpg
https://pasadenamag.com/wp-content/uploads/sites/69/2018/05/1365-South-Los-Robles-Pasadena-3.jpg
https://www.priceypads.com/wp-content/uploads/2020/03/a1f33f3f713f31e525adcf69db71c3fdl-m2029351381xd-w1020_h770_q80-1-696x368.jpg
https://i2.wp.com/www.cellaarchitecture.com/wp-content/uploads/2019/08/Laurelhurst-Tudor-Revival-14.jpg?fit=1030%2C687&ssl=1
https://lh3.googleusercontent.com/proxy/G9nddJECfMWEPW9EkvtBUzVqkvLuNgvkUThHlYKzdbhYoqeCa3Di9XWKEB0jq4hXIJTmDsI10L_yLSSJNXpS2LuR5V4NMCFB8DFkXjUjGyg_GVBPgrzMsc7dqfC1e-kVRMv97vmOqVoleuHqXwMjTcytO3MxsUwNhKf-IeQQ0o0
https://cdn.vox-cdn.com/thumbor/obFb2tDRCDE4AgGu0QyOvq-TLpU=/0x0:2500x1667/1200x800/filters:focal(968x631:1368x1031)/cdn.vox-cdn.com/uploads/chorus_image/image/66162566/ERP_22_9.0.jpg
https://www.merrimackdesign.com/wp-content/uploads/2015/01/tudor-interior.jpg
https://historicphoenixdistricts.com/wp-content/uploads/2015/10/By-the-1940s-a-neighborhood-of-Tudor-style-homes-encircled-the-outskirts-of-every-major-urban-area-in-the-United-States..jpeg
https://img.particlenews.com/image.php?type=thumbnail_1024x576&url=0uglTJ_0Ng7YaKu00
https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Cragside2.JPG/185px-Cragside2.JPG
https://www.cincinnati-oh.gov/buildings/assets/Image/Tudor%20Revival.jpg
https://georgiacoast.files.wordpress.com/2020/03/historic-savannah-ga-tudor-revival-house-photograph-copyright-brian-brown-vanishing-coastal-georgia-usa-2020.jpg
https://www.antiquehomesmagazine.com/wp-content/uploads/2017/09/Antique-Homes-Magazine-Tudor-Revival-Feature-1.jpg
https://cdn.captivatinghouses.com/wp-content/uploads/2020/04/IMG_6497.jpg
WARNING:root:no src found for main image, using thumbnail
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcTzcWJ6KMcqytDvpIkhdJuqHI4tx5T3ux-To-otnRI2Q40duq59&usqp=CAU
https://craiganddavidhomes.com/wp-content/uploads/2019/02/tudor-1200x642.jpg
https://www.oldhousedreams.com/wp-content/uploads/2020/03/1-7346oakstreet0425.jpg
https://i.pinimg.com/originals/76/bb/8f/76bb8f13341d89ced1003d8d3df3ab03.jpg
https://twincompanies.com/wp-content/uploads/2013/07/tudor-revival-1b.jpg
https://luxesource.com/wp-content/uploads/2019/07/LX_PNW38_HOM_Brooke_DP_1338.jpg
https://patch.com/img/cdn20/users/44719/20180928/084135/styles/raw/public/processed_images/2786a05dd9bd298351c24b6468631633l-m0o.jpg
https://cdn10.phillymag.com/wp-content/uploads/sites/3/2019/12/house-for-sale-gladwyne-young-tudor-foyer-brightmls.png
https://cdn.vox-cdn.com/thumbor/ev_NxBrjlH4VWoqX-xmNFMgggpY=/1400x1400/filters:format(jpeg)/cdn.vox-cdn.com/uploads/chorus_asset/file/16344990/0287919_5_.jpg
https://i0.wp.com/www.gardenstogables.com/wp-content/uploads/2020/01/Lville.jpg
https://scoutrealtyco.com/wp-content/uploads/2015/07/tudor2.jpg
https://sites.google.com/site/buildingwatching/_/rsrc/1468872720629/styles/21-the-tudor/21b.%20Tudor%20%28Kitchener%29__small.jpg?height=300&width=400
https://www.merrimackdesign.com/wp-content/uploads/2015/01/Tudor_Revival-1.jpg
https://images-na.ssl-images-amazon.com/images/I/51P67G76C5L.jpg
https://www.wolfehomes.com/wp-content/uploads/2019/08/Tudor-Rev-1-web-1080x717.jpg
https://theoldhouselife.com/wp-content/uploads/2019/05/lex1.jpg
https://static-10.sinclairstoryline.com/resources/media/90bd7e56-7814-49cf-bfcb-40e33a6731e5-smallScale_Purcell_27.jpg?1558542623644
https://www.thelakotagroup.com/wp-content/uploads/2013/03/tudor-revival-house-designed-by-arthur-maiwurm-1036-franklin.jpeg
WARNING:root:no src found for main image, using thumbnail
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcQv_ixJgFPjLejSBGwFtL8mdfWptqCV7L6S2CIc_pN_abMg9QVc&usqp=CAU
https://3dwarehouse.sketchup.com/warehouse/v1.0/publiccontent/2d6acb86-a82f-44cd-b3ae-7028cd237146
https://live.staticflickr.com/8534/8695315936_1827d7ac66_b.jpg
https://cdn.jhmrad.com/wp-content/uploads/september-sun-house-talk-tudor-lovin_135966-670x400.jpg
https://cdn.captivatinghouses.com/wp-content/uploads/2020/03/IMG_5868.jpg
https://lh3.googleusercontent.com/proxy/6M23LYU-do2PwurbiFRXjJ632pXvlLB-8HK5F5Xpyd52c7kpxxiuqb5EW4_BlBkhq0pJZDrmx8w27Yj3LUJb2TxbqcO9kgnawT-Q0XxVdUUE-YDoStf4h3hq3_UrMEolY6WoCLRqd-th
https://www.oldhouses.com/images/lst/004/4065/XL_17287_100_4304.jpg
https://bloximages.newyork1.vip.townnews.com/richmond.com/content/tncms/assets/v3/editorial/3/ed/3ed96ce0-58ba-11e5-946e-933f6bd246ec/55f329e4f0c86.image.jpg?resize=1200%2C799
https://img.particlenews.com/image.php?type=thumbnail_1024x576&url=2mg0vq_0Ni31HTB00
https://architecturestylesusa.files.wordpress.com/2016/12/tudor-style-house-2.jpg?w=820&h=312&crop=1
https://www.priceypads.com/wp-content/uploads/2020/01/95d0c2c5190b6cf63931842933f58117l-m2473220861xd-w1020_h770_q80-1.jpg
https://www.cottagesgardens.com/content/uploads/data-import/70369264/3383-Pacific-Presidio-Wall-House-For-Sale-Entry.jpeg
https://images.squarespace-cdn.com/content/v1/52438a8fe4b037ef64cafbd9/1446481707969-EVUSF6TU62HG4L2BENCU/ke17ZwdGBToddI8pDm48kOdqGmIz2IoHePZ1FapTYwR7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z4YTzHvnKhyp6Da-NYroOW3ZGjoBKy3azqku80C789l0q7uY_gEAXjzYg1fYWS2heTP2QyBwcgFKuioaK8hx6rxITydofbxpYUymd9VrnDGsg/image-asset.jpeg
https://www.oldhousedreams.com/wp-content/uploads/2019/10/12-7329benbowdr.jpg
https://tulsahomeforsale.net/wp-content/uploads/2011/10/tudor-revival-home.jpg
https://www.historycolorado.org/sites/default/files/media/images/2017/tudor1.jpg
https://live.staticflickr.com/2904/14215486540_4be237c837_b.jpg
https://s3-production.bobvila.com/articles/wp-content/uploads/2018/11/Tudor_House_Traits.jpg
https://ca-times.brightspotcdn.com/dims4/default/13c9e4c/2147483647/strip/true/crop/2048x1151+0+0/resize/840x472!/quality/90/?url=https%3A%2F%2Fcalifornia-times-brightspot.s3.amazonaws.com%2F44%2F66%2Fde4b5efe664f646d2b5b8ed2578a%2Fla-1515809382-8c8qwl1ylx-snap-image
https://noehill.com/sanmateo/images/seven_oaks_san_mateo_thumb.jpg
https://lh3.googleusercontent.com/proxy/s32cDU2-Big3LYktQrp23sKZGaGditKnGTUiz0m7wJ3k8SIL1YUgf9wxrJNUXXUYaIJSBcLf-Jpw-G45xAh6tSdvhF4v5OwuADkL3gxjO8R3yE_hR7Jh1M2uz5bbtrCxOF_t7_2DXdUIZo1msAKWZ3hEGrgrS6nRDfVPsgdvcwOhH5isPg
https://img.particlenews.com/image.php?type=thumbnail_1024x576&url=2tj6zV_0NjyHv0N00
https://georgiacoast.files.wordpress.com/2020/03/kavanaugh-park-tudor-revival-house-photograph-copyright-brian-brown-vanishing-coastal-georgia-usa-2020.jpg
https://lh3.googleusercontent.com/proxy/kH0nCqxSDrdL-xKl5JOrp-tuXMm5S2ds7sIe_gGR-KZ5X1ztWXapAFvuZF1awnD_B-_ljh8sFohDQIgEU8igiMEF00f27kwvIT-fXMw4MtRQtJh098jJlCIPinRO
https://www.oldhouseonline.com/.image/ar_16:9%2Cc_fill%2Ccs_srgb%2Cfl_progressive%2Cg_faces:center%2Cq_auto:good%2Cw_620/MTcxMjI4MTExMzQwMzE2MzM5/ext-20191029_ohj_rwhc_003_s.jpg
https://i1.wp.com/www.hisour.com/wp-content/uploads/2018/05/Tudor-Revival-architecture.jpg?fit=960%2C640&ssl=1
https://i0.wp.com/www.christiesrealestate.com/blog/wp-content/uploads/2018/08/TodorHeader2_1_copy.jpg?resize=1600%2C550&ssl=1
https://hgtvhome.sndimg.com/content/dam/images/hgtv/fullset/2017/5/30/0/FOD17_Burnham-Design_Beverly-Hills-Home_1.jpg.rend.hgtvcom.616.440.suffix/1496158749696.jpeg
WARNING:root:no src found for main image, using thumbnail
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcSH-MQBnyoakTCwIXKVpGda5Xyh_Xtf64pgfNDZ8qlLNWsjCTX2&usqp=CAU
https://images.squarespace-cdn.com/content/v1/5a14a8436f4ca3e5e99ae40a/1516401109761-PJ5JP0LRQGDU3GQYU83H/ke17ZwdGBToddI8pDm48kFWxnDtCdRm2WA9rXcwtIYR7gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QPOohDIaIeljMHgDF5CVlOqpeNLcJ80NK65_fV7S1UcTSrQkGwCGRqSxozz07hWZrYGYYH8sg4qn8Lpf9k1pYMHPsat2_S1jaQY3SwdyaXg/HUFF--EXT-06.jpg?format=1000w
https://patch.com/img/cdn20/users/22891861/20170905/055114/styles/raw/public/processed_images/e1b01e730f4cd715e7a3047c02b06dc3l-m1o.jpg
https://www.buffaloah.com/a/archsty/tud/tud_295depew.JPG
https://www.priceypads.com/wp-content/uploads/2018/05/2-1024x681.jpg
https://noehill.com/sanmateo/images/coxhead_house_in_san_mateo_thumb.jpg
https://ewscripps.brightspotcdn.com/dims4/default/b9974ad/2147483647/strip/true/crop/640x360+0+60/resize/1280x720!/quality/90/?url=https%3A%2F%2Fmediaassets.wcpo.com%2Fphoto%2F2016%2F11%2F22%2FWCPO_Hometour_Mullaney_lede_1479842748029_50215211_ver1.0_640_480.jpg
https://candysdirt.com/wp-content/uploads/2018/04/4312-Lorraine-1-1024x683.jpg
https://www.merrimackdesign.com/wp-content/uploads/2015/01/tudor-exterior-walk.jpg
https://images.squarespace-cdn.com/content/v1/5756eb264c2f85a473c70cb8/1467299928329-UNIH8QBSCOSB40IM64XD/ke17ZwdGBToddI8pDm48kC6B14ITpvbMRQSWsLGxXhx7gQa3H78H3Y0txjaiv_0fQZQHeq0CwZe2fIqUUdZnbwCvjvxRDOQvYnFbaJd85oiRkc8WWEWt0LGCNbwWndZjOqpeNLcJ80NK65_fV7S1UW-MoS7wD2EsdnwyRf01ndzdEtPMg_xnrD6n3shV9D__UsS8w9mFY1glQ8e_7aXdkA/image-asset.jpeg
https://previews.123rf.com/images/helgidinson/helgidinson1411/helgidinson141100013/33357155-the-tudor-revival-architecture-of-the-20th-century-commonly-called-mock-tudor-in-the-uk-first-manife.jpg
https://www.vancouverheritagefoundation.org/wp-content/uploads/2014/01/tudor-revival_img_map.jpg
https://ca-times.brightspotcdn.com/dims4/default/12637fd/2147483647/strip/true/crop/600x398+0+0/resize/840x557!/quality/90/?url=https%3A%2F%2Fcalifornia-times-brightspot.s3.amazonaws.com%2F26%2F61%2F49c22d2e9efb97e0b6e23e8128f4%2Fla-fi-1218-home1-lw7trbpd
https://www.vintagehomesofdenver.com/artman/uploads/1/DSC_0160_2.JPG
https://www.antiquehomesmagazine.com/wp-content/uploads/2017/09/Antique-Homes-Tudor-revival-1024x683.jpg
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcQO9DXmPMIUp6NQZy5XY2JtaHvHey96aK9K-4G594_xGmaEQD7q&usqp=CAU
WARNING:root:no src found for main image, using thumbnail
https://architecturalhouseplans.com/wp-content/uploads/home-plan-images/picture-of-tudor-revival.jpg
WARNING:root:no src found for main image, using thumbnail
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcQRiBq_w6Bps5S1vw3iv03FyJwVaMwWcVKzNWxivYb6QsuzmbtU&usqp=CAU
WARNING:root:no src found for main image, using thumbnail
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcRAeOBwuDYi4k0YCNRvid7XZJ66UDbmtCU66VKSv44FLSYgcwHN&usqp=CAU
https://s3-production.bobvila.com/articles/wp-content/uploads/2018/11/Smaller_Tudor_Houses_Today.jpg
WARNING:root:no src found for main image, using thumbnail
https://encrypted-tbn0.gstatic.com/images?q=tbn%3AANd9GcRPnHMxzzlYorXfkrC7ckIsCrPYJUAoxAcoYaiy7VawlEOg8uaN&usqp=CAU
https://www.oldhousedreams.com/wp-content/uploads/2020/04/1-912mainst0415.jpg
https://i.ytimg.com/vi/fK4HeEjsNs0/maxresdefault.jpg
https://images.squarespace-cdn.com/content/v1/5756eb264c2f85a473c70cb8/1467299604508-512XPVXY5AURK75JAGQY/ke17ZwdGBToddI8pDm48kLTORZbRop8y9gURhe9BZbgUqsxRUqqbr1mOJYKfIPR7ghj6HvfcmhHlMvf2scXKb02BBJxBkQ8Cj-gOFOgR0OlCRW4BPu10St3TBAUQYVKcAmd8AnW9RVuPbZHlBTL-74cEASX1HUTQG5X2TuOOUwiTXrTN9Hr1_5YxHKvx9vgN/image-asset.jpeg
https://www.tracyking.com/images/ARTICLE_ART/RESOURCES/RESTORATION/Restoring-A-Tudor-Revival-Home-in-NELA.jpg
https://www.priceypads.com/wp-content/uploads/2019/11/b8893772c16e7fe3271acde34c59d24dl-m2438512009xd-w1020_h770_q80-1.jpg
"""