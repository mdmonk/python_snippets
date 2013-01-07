#!/usr/bin/python
# $Id$
#
# My implementation of problem 16-2: "Printing Neatly" from
# Introduction to Algorithms / Cormen, Leiserson, Rivest
#
# Want to split a list of words into lines s.t. when printed on a number of
# lines holding at most M characters we minimize the sum of the cubes of the
# blank spaces at the end of all but the last line.

import string

# The words to split.
words = string.split("""
Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean dictum
bibendum neque. Integer felis urna, fringilla id, ultrices eget, auctor id,
enim. Aliquam vitae wisi. Proin purus. Maecenas risus libero, cursus vel,
vestibulum et, pellentesque in, pede. Donec id felis pellentesque dui vulputate
viverra. Aenean enim dolor, eleifend et, vestibulum eget, congue a, nisl.
Suspendisse potenti. Proin euismod malesuada mi. Cum sociis natoque penatibus
et magnis dis parturient montes, nascetur ridiculus mus. Morbi ornare fringilla
purus. Donec risus. Fusce rutrum diam sit amet augue. In hac habitasse platea
dictumst. Morbi id dolor. Pellentesque habitant morbi tristique senectus et
netus et malesuada fames ac turpis egestas. Aliquam erat volutpat. Nullam
dictum wisi eu magna.
Vestibulum rhoncus. Sed sit amet mauris. Duis sit amet metus a nibh mollis
cursus. Mauris elementum lectus sed enim. Mauris mollis. Cras tincidunt. Cras
purus mauris, rutrum ut, porttitor a, egestas sit amet, tortor. Vivamus sit
amet quam. Sed pede. Etiam imperdiet tellus a velit. Vivamus imperdiet, nulla
in ullamcorper aliquet, lorem pede consectetuer risus, eget luctus lacus orci
ut velit. Sed nisl. Mauris ornare orci rhoncus nunc. Etiam adipiscing, libero
vel accumsan porta, enim felis dignissim felis, vitae semper risus erat ut
pede.
Donec quis orci. Nulla facilisi. Sed mattis, sapien vel gravida sollicitudin,
urna libero placerat nibh, non cursus wisi tortor nec leo. Cras tortor nibh,
cursus vitae, sagittis sed, dictum sed, magna. Lorem ipsum dolor sit amet,
consectetuer adipiscing elit. Donec sagittis, metus ut vestibulum egestas,
lorem metus eleifend urna, et lacinia purus urna in ligula. In hac habitasse
platea dictumst. Cum sociis natoque penatibus et magnis dis parturient montes,
nascetur ridiculus mus. Nunc vitae felis vel est scelerisque sagittis. Aenean
convallis mattis nunc. Donec cursus ante at dui. Mauris magna. Etiam magna. In
eu mauris non urna volutpat tincidunt. Suspendisse ultricies bibendum mi.
Mauris ut pede ut nulla consequat ultricies.
Vivamus quam ante, congue eu, tincidunt id, cursus eu, dui. Suspendisse
tristique aliquet tortor. Vivamus erat dui, cursus sed, convallis id, pharetra
eu, ipsum. Lorem ipsum dolor sit amet, consectetuer adipiscing elit.
Pellentesque venenatis scelerisque justo. Ut aliquet. Sed sapien quam, volutpat
at, ultricies at, venenatis nec, purus. Duis porttitor urna ut nisl. Vestibulum
ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Ut
venenatis nonummy wisi. Proin metus. Suspendisse interdum, est convallis auctor
tristique, purus odio mattis pede, sed vulputate felis tortor a nulla.
Suspendisse potenti. Aenean adipiscing. Praesent vel ligula. Maecenas at
turpis. Nunc volutpat pede quis tellus luctus molestie. Sed massa erat, cursus
ut, cursus non, aliquet non, magna. In dignissim imperdiet arcu.
Aliquam quis odio. Morbi odio dolor, vehicula eget, suscipit nec, venenatis
eget, libero. Nullam pede. Donec id purus nec orci ultrices facilisis. Sed vel
tellus vitae sapien dapibus condimentum. Aenean turpis orci, nonummy nec,
mattis eget, sollicitudin vitae, pede. Proin mollis neque vel nunc. Maecenas
eget lectus. Etiam a magna. Nunc turpis. Aliquam lorem velit, pretium vitae,
hendrerit tempus, nonummy in, leo. Integer vitae urna. Fusce vitae turpis.
Pellentesque ornare posuere turpis. Nullam non purus quis lorem euismod
commodo. Morbi at enim.
Praesent tincidunt, ante id blandit ultricies, diam ipsum tempus dui, sit amet
pulvinar augue massa in enim. Duis pretium lectus ut arcu. Aliquam non leo et
ipsum luctus sodales. Nunc id wisi vel tellus tincidunt tempus. In metus lorem,
feugiat in, sollicitudin vitae, iaculis a, odio. Aenean lectus sem, vehicula
at, consequat vel, tempor et, nulla. Proin ultrices elementum neque. In
consectetuer convallis velit. Duis urna. Donec ultricies accumsan nunc. Quisque
pretium odio ac massa. Duis nec nunc. Curabitur lacus justo, suscipit sed,
semper in, adipiscing in, quam. Phasellus consectetuer augue vel wisi. Nullam
lectus. In hac habitasse platea dictumst. Morbi a arcu a risus convallis
tincidunt. Duis sit amet nibh. Nullam magna dui, accumsan id, congue quis,
rhoncus eu, neque.
In condimentum, nibh et bibendum molestie, massa nunc iaculis arcu, id volutpat
elit elit nec tortor. Pellentesque habitant morbi tristique senectus et netus
et malesuada fames ac turpis egestas. Pellentesque habitant morbi tristique
senectus et netus et malesuada fames ac turpis egestas. Curabitur eleifend
lorem laoreet est. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. In
ac diam. Nulla hendrerit mattis lectus. Nulla enim. Sed vel tortor. Donec
lectus arcu, dictum et, fermentum sed, rutrum id, ipsum. Nunc porta interdum
ante. Pellentesque laoreet dolor a velit. Pellentesque consectetuer rhoncus
nibh. Vestibulum lacus nisl, scelerisque vitae, vehicula ultricies, tincidunt
ut, orci.
Curabitur vulputate sapien eget lacus. Duis ante orci, malesuada vestibulum,
interdum sit amet, egestas at, ipsum. Suspendisse potenti. Mauris feugiat
sagittis tellus. Etiam luctus wisi a eros. Quisque pellentesque blandit purus.
Curabitur eu nisl id mi eleifend pharetra. Donec ornare diam id lacus. Aenean
sit amet justo. Sed tincidunt, quam ut feugiat dignissim, nisl mauris tempor
wisi, at pretium urna lectus a turpis. Donec quis dolor vel ipsum sodales
adipiscing. Donec sagittis. Aliquam non velit quis eros vehicula porta.
Phasellus eu massa at sem dapibus consectetuer. Aliquam erat volutpat. Nam
malesuada imperdiet nisl. Donec ac neque at urna feugiat porttitor. Fusce velit
dui, vehicula quis, venenatis quis, lacinia quis, tortor. Donec blandit, quam
ut vehicula volutpat, enim pede accumsan augue, sit amet auctor nunc quam ac
erat. Nunc iaculis quam eu magna.
Integer ultrices quam vel urna. Vivamus bibendum porta lectus. Vivamus
bibendum, leo vel tempor porta, tortor elit posuere neque, vel egestas elit mi
quis massa. Vestibulum et ante eget nisl condimentum luctus. Proin iaculis
auctor tortor. Nam quis tortor. Cras nisl. Cras scelerisque lectus at felis.
Etiam sit amet felis. Class aptent taciti sociosqu ad litora torquent per
conubia nostra, per inceptos hymenaeos. Pellentesque lacus est, commodo id,
sagittis vitae, bibendum vitae, nunc. Vivamus vel libero. Sed et justo. Fusce
ipsum. In consequat metus vel velit porta volutpat. Maecenas venenatis
tincidunt tellus. Fusce viverra. Integer lorem.
Phasellus tempor nisl vel lacus. Phasellus diam. Fusce id elit. In at nisl eget
mauris venenatis mollis. Proin nec nisl. Praesent consequat pede vel metus.
Vivamus dignissim lectus ut metus. Quisque semper, turpis vitae scelerisque
fringilla, est sem sodales odio, at commodo est magna in velit. Quisque turpis.
Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere
cubilia Curae; Vestibulum lectus diam, sagittis et, dignissim sed, sodales
quis, magna. Aenean eget dui. Cum sociis natoque penatibus et magnis dis
parturient montes, nascetur ridiculus mus.
""")

# The number of characters per line.
charsPerLine = 60

# Python doesn't seem to have an infinity; we'll make do with this.
# (Any larger than 2**30-1 and jython gives OverflowErrors. And too large
# and CPython becomes slower, since it needs more storage space.)
Inf = 2**30-1

class UpperTriangularMatrix:
    """
    An upper triangular n*n matrix.
    (An upper triangular matrix is one in which all elements below the main
    diagonal are zero.)
    This is stored as an array of size \sum_{i=1}^n i (= n*(n+1)//2)
    Element (i,j) is stored at position \sum_{k=1}^i (n-k)
    (= i*n - i*(i+1)//2)
    """

    def __init__(self, n, initialValue):
        assert n >= 0
        self.n = n
        self.array = [initialValue for i in range(n*(n+1)/2)]

    def set(self,i,j,v):
        assert 0 <= i and i <= j and j < self.n
        self.array[i*self.n - i*(i+1)/2 + (j-1)] = v

    def get(self,i,j):
        assert 0 <= i and i <= j and j < self.n
        return self.array[i*self.n - i*(i+1)/2 + (j-1)]

# lineCost[i][j] <- cost of a line containing words[i:j+1]
lineCost = UpperTriangularMatrix(len(words), Inf)
for i in range(0, len(words)):
    charsUsed = -1
    for j in range(i, len(words)):
        charsUsed += len(words[j]) + 1
        if charsUsed > charsPerLine:
            break
        if j == len(words)-1:
            lineCost.set(i,j, 0) # last line costs nothing
        else:
            lineCost.set(i,j, (charsPerLine - charsUsed) ** 3)

# minimumCost[i] <- minimum cost of printing first i words.
# minimumCost[i] <- min for j in [1, i) { minimumCost[j-1]+lineCost[j-1][i-1] }
minimumCost = [0] + [Inf for i in range(len(words)+1)]
lineBoundaries = [[] for i in range(len(words)+2)]
for i in range(1, len(words)+1):
    for j in range(1, i):
        if minimumCost[j-1] + lineCost.get(j-1,i-1) < minimumCost[i]:
           minimumCost[i] = minimumCost[j-1] + lineCost.get(j-1,i-1)
           lineBoundaries[i] = lineBoundaries[j-1] + [j-1]

minimumCost = minimumCost[len(words)]
lineBoundaries = lineBoundaries[len(words)]
lineBoundaries.append(len(words))

for i in range(1, len(lineBoundaries)):
    print string.join(words[lineBoundaries[i-1]:lineBoundaries[i]], ' ')
