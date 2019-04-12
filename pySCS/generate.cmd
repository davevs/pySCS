python pySCS.py %1 --dfd | dot -Tpng -o %1\dfd.png
python pySCS.py %1 --seq | java -Djava.awt.headless=true -jar plantuml.jar -tpng -pipe > %1\seq.png
python pySCS.py %1 --report template.md | pandoc -f markdown -t html > %1\report.html