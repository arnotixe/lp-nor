dist: en hu_HU ru_RU la
	rm -f META-INF/* dialog/* pythonpath/*
	zip -r lightproof-`cat VERSION`.zip *_*.oxt META-INF dialog pythonpath \
	VERSION* data NEWS ChangeLog* TODO THANKS *_py.py Dialog.py Compile.py \
	Makefile README* make.py Linguistic_xcu.py description_xml.py doc

hu_HU:
	make clean
	python make.py -v `grep hu_HU VERSIONS | cut -d ' ' -f 2` -d data hu_HU
	zip -r lightproof-hu_HU-`grep hu_HU VERSIONS | cut -d ' ' -f 2`.oxt \
	META-INF pythonpath dialog Lightproof.py *xcu *xml README_hu_HU ChangeLog_hu_HU

en:
	make clean
	python make.py -v `grep en VERSIONS | cut -d ' ' -f 2` -d data en en-GB,en-US,en-PH,en-ZA,en-NA,en-ZW,en-AU,en-CA,en-IE,en-IN,en-BZ,en-BS,en-GH,en-JM,en-NZ,en-TT
	zip -r lightproof-en-`grep en VERSIONS | cut -d ' ' -f 2`.oxt \
	META-INF pythonpath dialog Lightproof.py *xcu *xml README_en

ru_RU:
	make clean
	python make.py -v `grep ru_RU VERSIONS | cut -d ' ' -f 2` -d data ru_RU
	zip -r lightproof-ru_RU-`grep ru_RU VERSIONS | cut -d ' ' -f 2`.oxt \
	META-INF pythonpath dialog Lightproof.py *xcu *xml README_ru_RU

la:
	make clean
	python make.py -v `grep la VERSIONS | cut -d ' ' -f 2` -d data la
	zip -r lightproof-la-`grep la VERSIONS | cut -d ' ' -f 2`.oxt \
	META-INF pythonpath dialog Lightproof.py *xcu *xml README_la

clean:
	@rm -f pythonpath/* dialog/*
