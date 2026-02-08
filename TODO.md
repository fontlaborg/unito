# 1. Analyze old project

./external/unito/ is the old project which we want to refactor into this project that follows the Google Fonts template structure and is hosted at https://github.com/fontlaborg/unito-font/ 

Analyze the old project and understand how it works.

Understand that we want to put the final deliverables into ./fonts/ folder 

Understand that we want to put the built fonts into ./sources/ as well, and inside ./sources/ we want to create subfolders for the input fonts, and we want an updated ./sources/config.yaml for the 4 fonts we aim to build (Unito Regular, Unito Bold, Unicode Condensed, Unicode Bold Condensed). 

We want to adapt external/unito/unito.py and external/unito/unito.sh into a robust extensive package hosted right here in this repo under ./src/unito/ and then inside ./scripts/ must be a script that runs the package with the fonts. 

We want to update everything including: AUTHORS.txt CONTRIBUTORS.txt CONTRIBUTORS.txt README.md renovate.json documentation/

Port the requirements files to a python project yaml and get rid of the old requirements files. 

Write a CLAUDE.md and AGENTS.md that explains this project and how to extend it. 

Don’t hardcode the files in the scripts, make a nice yaml that replicates the info below. 

Update .github/workflows/build.yaml 

# Update the tool 

The toolkit needs to be updated so that it first downloads the fonts from the repos instead of from the local folders, but stores them locally and performs the conversions. Also make additional caching that just saves the instantiated fonts into a cache folder. 

Add CLI flag --force that forces re-downloading the fonts from the repos/pages, and re-running the conversions disregarding the caches. 

By default build the fonts in --hang --hani mode

Make sure to include files like ./external/unito/01in/hani/Hani.jsonl in the main repo because we’ll untimately get rid of ./external/ (which is temporary). 

# Obtain the fonts

## Repo

https://github.com/google/fonts/tree/main/ofl/

## Files to be placed in the 01in folders

### 01

notosans/NotoSans[wdth,wght].ttf

### 02

notoemoji/NotoEmoji[wght].ttf
notosanssymbols/NotoSansSymbols[wght].ttf
notosanssymbols2/NotoSansSymbols2-Regular.ttf

### 03

notomusic/NotoMusic-Regular.ttf
notosansadlam/NotoSansAdlam[wght].ttf
notosansanatolianhieroglyphs/NotoSansAnatolianHieroglyphs-Regular.ttf
notosansarabic/NotoSansArabic[wdth,wght].ttf
notosansarmenian/NotoSansArmenian[wdth,wght].ttf
notosansavestan/NotoSansAvestan-Regular.ttf
notosansbalinese/NotoSansBalinese[wght].ttf
notosansbamum/NotoSansBamum[wght].ttf
notosansbassavah/NotoSansBassaVah[wght].ttf
notosansbatak/NotoSansBatak-Regular.ttf
notosansbengali/NotoSansBengali[wdth,wght].ttf
notosansbhaiksuki/NotoSansBhaiksuki-Regular.ttf
notosansbrahmi/NotoSansBrahmi-Regular.ttf
notosansbuginese/NotoSansBuginese-Regular.ttf
notosansbuhid/NotoSansBuhid-Regular.ttf
notosanscanadianaboriginal/NotoSansCanadianAboriginal[wght].ttf
notosanscarian/NotoSansCarian-Regular.ttf
notosanscaucasianalbanian/NotoSansCaucasianAlbanian-Regular.ttf
notosanschakma/NotoSansChakma-Regular.ttf
notosanscham/NotoSansCham[wght].ttf
notosanscherokee/NotoSansCherokee[wght].ttf
notosanschorasmian/NotoSansChorasmian-Regular.ttf
notosanscoptic/NotoSansCoptic-Regular.ttf
notosanscuneiform/NotoSansCuneiform-Regular.ttf
notosanscypriot/NotoSansCypriot-Regular.ttf
notosanscyprominoan/NotoSansCyproMinoan-Regular.ttf
notosansdeseret/NotoSansDeseret-Regular.ttf
notosansdevanagari/NotoSansDevanagari[wdth,wght].ttf
notosansduployan/NotoSansDuployan-Regular.ttf
notosansegyptianhieroglyphs/NotoSansEgyptianHieroglyphs-Regular.ttf
notosanselbasan/NotoSansElbasan-Regular.ttf
notosanselymaic/NotoSansElymaic-Regular.ttf
notosansethiopic/NotoSansEthiopic[wdth,wght].ttf
notosansgeorgian/NotoSansGeorgian[wdth,wght].ttf
notosansglagolitic/NotoSansGlagolitic-Regular.ttf
notosansgothic/NotoSansGothic-Regular.ttf
notosansgrantha/NotoSansGrantha-Regular.ttf
notosansgujarati/NotoSansGujarati[wdth,wght].ttf
notosansgunjalagondi/NotoSansGunjalaGondi[wght].ttf
notosansgurmukhi/NotoSansGurmukhi[wdth,wght].ttf
notosanshanifirohingya/NotoSansHanifiRohingya[wght].ttf
notosanshanunoo/NotoSansHanunoo-Regular.ttf
notosanshatran/NotoSansHatran-Regular.ttf
notosanshebrew/NotoSansHebrew[wdth,wght].ttf
notosansimperialaramaic/NotoSansImperialAramaic-Regular.ttf
notosansindicsiyaqnumbers/NotoSansIndicSiyaqNumbers-Regular.ttf
notosansinscriptionalpahlavi/NotoSansInscriptionalPahlavi-Regular.ttf
notosansinscriptionalparthian/NotoSansInscriptionalParthian-Regular.ttf
notosansjavanese/NotoSansJavanese[wght].ttf
notosanskaithi/NotoSansKaithi-Regular.ttf
notosanskannada/NotoSansKannada[wdth,wght].ttf
notosanskawi/NotoSansKawi[wght].ttf
notosanskayahli/NotoSansKayahLi[wght].ttf
notosanskharoshthi/NotoSansKharoshthi-Regular.ttf
notosanskhmer/NotoSansKhmer[wdth,wght].ttf
notosanskhojki/NotoSansKhojki-Regular.ttf
notosanskhudawadi/NotoSansKhudawadi-Regular.ttf
notosanslao/NotoSansLao[wdth,wght].ttf
notosanslepcha/NotoSansLepcha-Regular.ttf
notosanslimbu/NotoSansLimbu-Regular.ttf
notosanslineara/NotoSansLinearA-Regular.ttf
notosanslinearb/NotoSansLinearB-Regular.ttf
notosanslisu/NotoSansLisu[wght].ttf
notosanslycian/NotoSansLycian-Regular.ttf
notosanslydian/NotoSansLydian-Regular.ttf
notosansmahajani/NotoSansMahajani-Regular.ttf
notosansmalayalam/NotoSansMalayalam[wdth,wght].ttf
notosansmandaic/NotoSansMandaic-Regular.ttf
notosansmanichaean/NotoSansManichaean-Regular.ttf
notosansmarchen/NotoSansMarchen-Regular.ttf
notosansmasaramgondi/NotoSansMasaramGondi-Regular.ttf
notosansmath/NotoSansMath-Regular.ttf
notosansmayannumerals/NotoSansMayanNumerals-Regular.ttf
notosansmedefaidrin/NotoSansMedefaidrin[wght].ttf
notosansmeeteimayek/NotoSansMeeteiMayek[wght].ttf
notosansmendekikakui/NotoSansMendeKikakui-Regular.ttf
notosansmeroitic/NotoSansMeroitic-Regular.ttf
notosansmiao/NotoSansMiao-Regular.ttf
notosansmodi/NotoSansModi-Regular.ttf
notosansmongolian/NotoSansMongolian-Regular.ttf
notosansmono/NotoSansMono[wdth,wght].ttf
notosansmro/NotoSansMro-Regular.ttf
notosansmultani/NotoSansMultani-Regular.ttf
notosansmyanmar/NotoSansMyanmar[wdth,wght].ttf
notosansnabataean/NotoSansNabataean-Regular.ttf
notosansnagmundari/NotoSansNagMundari[wght].ttf
notosansnandinagari/NotoSansNandinagari-Regular.ttf
notosansnewa/NotoSansNewa-Regular.ttf
notosansnewtailue/NotoSansNewTaiLue[wght].ttf
notosansnko_todelist/NotoSansNKo-Regular.ttf
notosansnko/NotoSansNKo-Regular.ttf
notosansnkounjoined/NotoSansNKoUnjoined[wght].ttf
notosansnushu/NotoSansNushu-Regular.ttf
notosansogham/NotoSansOgham-Regular.ttf
notosansolchiki/NotoSansOlChiki[wght].ttf
notosansoldhungarian/NotoSansOldHungarian-Regular.ttf
notosansolditalic/NotoSansOldItalic-Regular.ttf
notosansoldnortharabian/NotoSansOldNorthArabian-Regular.ttf
notosansoldpermic/NotoSansOldPermic-Regular.ttf
notosansoldpersian/NotoSansOldPersian-Regular.ttf
notosansoldsogdian/NotoSansOldSogdian-Regular.ttf
notosansoldsoutharabian/NotoSansOldSouthArabian-Regular.ttf
notosansoldturkic/NotoSansOldTurkic-Regular.ttf
notosansoriya/NotoSansOriya[wdth,wght].ttf
notosansosage/NotoSansOsage-Regular.ttf
notosansosmanya/NotoSansOsmanya-Regular.ttf
notosanspahawhhmong/NotoSansPahawhHmong-Regular.ttf
notosanspalmyrene/NotoSansPalmyrene-Regular.ttf
notosanspaucinhau/NotoSansPauCinHau-Regular.ttf
notosansphagspa/NotoSansPhagsPa-Regular.ttf
notosansphoenician/NotoSansPhoenician-Regular.ttf
notosanspsalterpahlavi/NotoSansPsalterPahlavi-Regular.ttf
notosansrejang/NotoSansRejang-Regular.ttf
notosansrunic/NotoSansRunic-Regular.ttf
notosanssamaritan/NotoSansSamaritan-Regular.ttf
notosanssaurashtra/NotoSansSaurashtra-Regular.ttf
notosanssharada/NotoSansSharada-Regular.ttf
notosansshavian/NotoSansShavian-Regular.ttf
notosanssiddham/NotoSansSiddham-Regular.ttf
notosanssignwriting/NotoSansSignWriting-Regular.ttf
notosanssinhala/NotoSansSinhala[wdth,wght].ttf
notosanssogdian/NotoSansSogdian-Regular.ttf
notosanssorasompeng/NotoSansSoraSompeng[wght].ttf
notosanssoyombo/NotoSansSoyombo-Regular.ttf
notosanssundanese/NotoSansSundanese[wght].ttf
notosanssunuwar/NotoSansSunuwar-Regular.ttf
notosanssylotinagri/NotoSansSylotiNagri-Regular.ttf
notosanssyriac/NotoSansSyriac[wght].ttf
notosanssyriaceastern/NotoSansSyriacEastern[wght].ttf
notosanssyriacwestern/NotoSansSyriacWestern[wght].ttf
notosanstagalog/NotoSansTagalog-Regular.ttf
notosanstagbanwa/NotoSansTagbanwa-Regular.ttf
notosanstaile/NotoSansTaiLe-Regular.ttf
notosanstaitham/NotoSansTaiTham[wght].ttf
notosanstaiviet/NotoSansTaiViet-Regular.ttf
notosanstakri/NotoSansTakri-Regular.ttf
notosanstamil/NotoSansTamil[wdth,wght].ttf
notosanstamilsupplement/NotoSansTamilSupplement-Regular.ttf
notosanstangsa/NotoSansTangsa[wght].ttf
notosanstc/NotoSansTC[wght].ttf
notosanstelugu/NotoSansTelugu[wdth,wght].ttf
notosansthaana/NotoSansThaana[wght].ttf
notosansthai/NotoSansThai[wdth,wght].ttf
notosanstifinagh/NotoSansTifinagh-Regular.ttf
notosanstirhuta/NotoSansTirhuta-Regular.ttf
notosansugaritic/NotoSansUgaritic-Regular.ttf
notosansvai/NotoSansVai-Regular.ttf
notosansvithkuqi/NotoSansVithkuqi[wght].ttf
notosanswancho/NotoSansWancho-Regular.ttf
notosanswarangciti/NotoSansWarangCiti-Regular.ttf
notosansyi/NotoSansYi-Regular.ttf
notosanszanabazarsquare/NotoSansZanabazarSquare-Regular.ttf
notoserifahom/NotoSerifAhom-Regular.ttf
notoserifdivesakuru/NotoSerifDivesAkuru-Regular.ttf
notoserifdogra/NotoSerifDogra-Regular.ttf
notoserifhentaigana/NotoSerifHentaigana[wght].ttf
notoserifkhitansmallscript/NotoSerifKhitanSmallScript-Regular.ttf
notoserifmakasar/NotoSerifMakasar-Regular.ttf
notoserifnyiakengpuachuehmong/NotoSerifNyiakengPuachueHmong[wght].ttf
notoserifolduyghur/NotoSerifOldUyghur-Regular.ttf
notoserifottomansiyaq/NotoSerifOttomanSiyaq-Regular.ttf
notoseriftangut/NotoSerifTangut-Regular.ttf
notoseriftibetan/NotoSerifTibetan[wght].ttf
notoseriftodhri/NotoSerifTodhri-Regular.ttf
notoseriftoto/NotoSerifToto[wght].ttf
notoserifyezidi/NotoSerifYezidi[wght].ttf
nototraditionalnushu/NotoTraditionalNushu[wght].ttf
notoznamennymusicalnotation/NotoZnamennyMusicalNotation-Regular.ttf

### 04

notosanskr/NotoSansKR[wght].ttf
notosanssc/NotoSansSC[wght].ttf

## Repo 

https://github.com/stgiga/UnifontEX/tree/main

### 05

UnifontExMono.ttf

## Page

https://unifoundry.com/pub/unifont/

Locate the newest subfolder, which at this point is 

https://unifoundry.com/pub/unifont/unifont-17.0.03/ 

and then inside 

https://unifoundry.com/pub/unifont/unifont-17.0.03/font-builds/

get https://unifoundry.com/pub/unifont/unifont-17.0.03/font-builds/unifont-17.0.03.otf and convert to ttf with otf2ttf (part of the 'afdko' package you must install)

get https://unifoundry.com/pub/unifont/unifont-17.0.03/font-builds/unifont_upper-17.0.03.otf and convert to ttf with otf2ttf (part of the 'afdko' package you must install)

### 06

place the two ttf files

