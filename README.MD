Click on 'Auto' to toggle to 'Manual'
* Auto will execute PLC commands, setting of MV101 and P101 states based on LIT101 values 
* Manual allows for toggling and setting of MV101 and P101, not affected by LIT101 values
* 'attack.txt' contains the space delimited deltas. Which will be randomly chosen to add to LIT101
* 'cusum.txt' contains the parameters bias and threshold respectively space delimited
*'attacktype' contains the constant to indicate the type of attack that is ongoing. Can be 'BIAS', 'SURGE'
'outputs' contains the results of the simulator in the format:
(f"{BIAS},{TAU},{ATTACKS},{DETECTED},{round(CUSUM,4)},{FALSE_ALARMS}\n")