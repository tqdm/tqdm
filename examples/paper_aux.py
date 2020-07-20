# tqdm paper contributors name list duplicates checker and alphabetical reorder
# by Stephen Karl Larroque
# Licensed under MIT Public License

def checkdup(L):
    s = set()
    duplist = []
    for i, e in enumerate(L):
        if e in s:
            duplist.append(i)
        else:
            s.add(e)
    return duplist

def sortidx(L):
    return [i[0] for i in sorted(enumerate(L), key=lambda x:x[1])]

# Input list of names separated by commas (from https://github.com/tqdm/tqdm/pull/905 )
s = "Martin Zugnoni, Guangshuo Chen, Hadrien Mary (orcid: 0000-0001-8199-5932), Kyle Altendorf, Ivan Ivanov, James E. King, Mikhail Korobov, Daniel Panteleit, Matthew D. Pagel, James Lu, Hugo van Kemenade (orcid: 0000-0001-5715-8632), Igor Ljubuncic, Adnan Umer, Johannes Hansen, Charles Newey, Veith Röthlingshöfer (orcid: 0000-0002-1824-3153), FichteFoll, Mikhail Dektyarev, Chung-Kai Hung, Greg Gandenberger, Min ho Kim, Thomas A. Caswell, Orivej Desh, Kuang-che Wu, Alexander Plavin (orcid: 0000-0003-2914-8554), zz, Sepehr Sameni, David W. H. Swenson, ReadmeCritic, stonebig, Cheng Chen, Staffan Malmgren, Sergei Izmailov, Anurag Pandey, Peter VandeHaar, Alex Rothberg, Carlin MacKenzie (orcid: 0000-0002-9300-0741), Edward Betts, Socialery, Dyno Fu, Jack McCracken, Jose Tiago Macara Coutinho, Lev Velykoivanenko, Albert Kottke, Fabian Dill, Ford Hurley, Shirish Pokharel, David Bau, mjstevens777, mbargull, Marcel Bargull, immerrr, Mike Kutzma, Yaroslav Halchenko, Antony Lee, Julien Chaumont, Gareth Simons, Max Nordlund, William Turner, Jesús Cea, darindf, Robert Krzyzanowski, toddrme2178, Andrey Portnoy, Arun Persaud, Daniel King, deeenes, Jan Schlüter, Javi Merino, Josh Karpel, Riccardo Coccioli, Pablo Zivic, Rafael Lukas Maers, Tomas Ostasevicius, zed, CrazyPython, littlezz"

# Split each name in a list
s2 = s.split(", ")
# Get last name
import re
g = [re.search(r'(\S+)(\s+\(orcid.+)?$', x).group(1) if ' ' in x else x for x in s2]
# Check last name duplicates (you'll need to fix manually because it can't be done automatically, multiple people can have the same last name)
d = checkdup(g)
g2 = [g[x] for x in d]
# Sort by last name
sidx = sortidx(g)
s3 = [s2[x] for x in sidx]
# Save result in a text file
with open('out.txt', 'w') as f:
    f.write(",\n".join(s3))
