
all:
	@echo "Usage: make [target] -- where target is one of: 'git' 'doc' 'clean 'sum' "

# Genetrate checksum (recommend Whole project clean before)

get:
	cp -a ../IOCOMx/CAN/robotell/ ./source_code
	rm -rf source_code/robotell/python-can/.git

# Auto Checkin

ifeq ("$(AUTOCHECK)","")
AUTOCHECK=autocheck
endif

git:
	git add .
	git commit -m "$(AUTOCHECK)"
	git push

# Documentation

doc:
	(cd wclock; doxygen; cd ..)



