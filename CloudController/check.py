import difflib
from difflib import unified_diff
import diff_match_patch 

#s1 = ['bacon\n', 'eggs\n', 'ham\n', 'guido\n']
#s2 = ['python\n', 'eggs\n', 'hamster\n', 'guido\n']
s1 = 'Hamlet: Do you see yonder cloud that\'s almost in shape of a camel?Polonius: By the mass, and \'tis like a camel, indeed.Hamlet: Methinks it is like a weasel.Polonius: It is backed like a weasel.Hamlet: Or like a whale?Polonius: Very like a whale.-- Shakespeare'
s2 = 'Hamlet: Do you see the cloud over there that\'s almost in shape of a camel?Polonius: By the mass, and \'tis like a camel, indeed.Hamlet: Methinks it is like a weasel.Polonius: It is backed like a weasel.Hamlet: Or like a whale?Polonius: Very like a whale.--Shakespeare'

print len(s2)
# var = unified_diff(s1, s2, n=0)
# check  = ''
# print var[1]
# kaam = diff_match_patch.diff_match_patch()
# diffs = kaam.diff_main(s1, s2) 
# #print diffs

# for line in kaam.patch_make(diffs):
# 	print line
#print kaam.patch_apply(kaam.patch_make(diffs) , s2)

var = diff_match_patch.diff_match_patch()

diff = var.diff_main(s1,s2, True)
if len(diff) > 2:
	var.diff_cleanupSemantic(diff)



patch_list = var.patch_make(s1, s2, diff)
patch_text = var.patch_toText(patch_list)

print '-----------------------'
print len(patch_text)
print '------------------------'



patches = var.patch_fromText(patch_text)
results = var.patch_apply(patches, s1)



print results[0]