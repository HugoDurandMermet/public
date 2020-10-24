# This is the default value we want for the function call indicator.
forcePerfTimers.has_been_called = False
 
# Here's our main function, forcing the Performance Timers to update
# in one call.
def forcePerfTimers():
    
    # Set a condition in case the Performance Timers haven't been enabled
    # yet.
    if nuke.usingPerformanceTimers() == False:
        nuke.startPerformanceTimers()
        
    # And another one, if they're currently enabled.
    elif nuke.usingPerformanceTimers() == True: 
        nuke.resetPerformanceTimers()
        
    # Make a loop to iterate through all nodes currently in the script.
    for m in nuke.allNodes():
        
        # Target only those who already have a 'mix' knob.
        if m.knob('mix'):
            
            # The value we'll set has no other purpose than to be a
            # random float number. After some experiments, I've concluded
            # this is the best way to force the Performance Timers to
            # deliver their values on your nodes.
            m['mix'].setValue(0.5555)
            
            # We'll call an updateUI() and the clear all caches function,
            # in order to force an update and get rid of the previous value
            # (thx to Ben McEwan for the tip).
            nuke.menu('Nuke').findItem('Cache/Clear All').invoke()
            nuke.updateUI()
            
            # And we'll put back the mix at 1. This is of course assuming all
            # nodes are at 1, which is the case for this experiment. If later
            # on, I'll need to integrate this snippet into a larger proper Py
            # script, we'll need to make a dictionary collecting the mix values
            # with their node names as the keys to put them back as they were
            # before (not sure if this sentence makes much sense in English though)
            m['mix'].setValue(1)
            
    # Time to set our function call indicator as True.
    forcePerfTimers.has_been_called = True
 
# And place a condition in case the function hasn't been called.
if __name__ =='__main__': 
    forcePerfTimers.has_been_called = False
 
# Let's call our forcePerfTimers function then.
forcePerfTimers()
 
# This ain't mandatory but for research purposes,
# it might be a good idea to check our indicator's
# value.
print forcePerfTimers.has_been_called
# This is our second function we want to run, based
# on the info we can collect after the forcePerfTimers
# one.
def printPerfInfo():
    
    # We can now condition this function to the value
    # of the indicator we've made. If forcePerfTimers
    # has been called, we can go on with the rest of
    # this function.
    if forcePerfTimers.has_been_called == True:
        
        # This is a function I directly copied from the
        # Foundry Performance Timers page, to display 
        # the performance info of all nodes in the script.
        for n in nuke.allNodes(recurseGroups = True):
            print n.fullName()
            print n.performanceInfo()
    # And if the forcePerfTimers has not been called,
    # then print a message warning this didn't work.
    elif forcePerfTimers.has_been_called == False:
        print "Didn't work, sorry mate :("

