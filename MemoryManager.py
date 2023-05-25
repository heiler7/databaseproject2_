# encoding: utf-8
# @Time : 2022/5/26 23:46
# @Author : Neesky
# @contact: neesky@foxmail.com
# @File : MemoryManager.py
# @Software: PyCharm
import os
import pandas as pd
class MemoryManager:
    def __init__(self,root = "./"):
        self.root = root
        self.blockNum = 100
        self.blockSize = 4096
        self.TableBlockPath = os.path.join(self.root, "TableBlocks.csv")
        self.MemoryBlockPath = os.path.join(self.root, "MemoryBlocks")
        self.BlockDelPath = os.path.join(self.MemoryBlockPath,"BlockDel.csv")

        if (os.path.isdir(self.MemoryBlockPath) == False):
            os.makedirs(self.MemoryBlockPath)

        with open(self.BlockDelPath ,"w") as file1:
            file1.write("blockAddr,delColumn\n")
        with open(self.TableBlockPath ,"w") as file1:
            file1.write("blockAddr,blockRemain\n")
            for i in range(self.blockNum):
                file1.write(os.path.join(self.MemoryBlockPath, str(i) + ".csv")+ "," + str(self.blockSize)+"\n")
                with open(os.path.join(self.MemoryBlockPath, str(i) + ".csv"), "w") as file:  # 新建block文件
                    pass

    # 空间清除
    def subMomeryBlock(self,whichBlock,noNeedLines:list,varSize): ##可以一次删除多个
        tb = pd.read_csv(self.TableBlockPath)
        print(tb.loc[0,"blockRemain"])
        tb.loc[eval(whichBlock.split("\\")[-1].split(".")[0]),"blockRemain"] += varSize
        tb.to_csv(self.TableBlockPath, index=False, sep=',')  # 找到空隙了，写入


#fixme 添加到一个表，里面可以放已经被删除的行。这样就可以直接覆盖了
        # with open(whichBlock, "r+") as file:
        #     lines = file.readlines()
        #     file.seek(0,0)
        #     file.truncate()
        #     reLines = []
        #     for i in range(len(lines)):
        #         if i not in noNeedLines:
        #             reLines.append(lines[i])
        #     file.writelines(reLines)
        return True
    
    # 寻找块
    def findMomeryBlock(self,whichBlock,needLines:list): # needLines为多个line
        reLine = []
        with open(whichBlock, "r+") as file:
            lines = file.readlines()
            reLine = [lines[need].rstrip() for need in needLines]
        return reLine

    # 更新
    def updataMomeryBlock(self,whichBlock,updataLines:list,updataVarList:list): # needLines为多个line
        reLine = []
        with open(os.path.join(self.MemoryBlockPath, str(whichBlock) + ".csv"), "r+") as file:
            lines = file.readlines()
            for i in range(len(updataLines)):
                lines[i] = ",".updataVarList[i]
        return lines

    # 块被使用，加上size
    def addMomeryBlock(self, varList , varSize):
        # 其实可以在外部处理，里面只需要reList
        # dic是所有变量及对应的值，var是所有变量以及对应的字段
        tb = pd.read_csv(self.TableBlockPath)
        ls = tb['blockRemain'].tolist()
        whichBlock = -1
        for i in range(len(ls)):
            if (ls[i] >= varSize):
                tb.loc[i, 'blockRemain'] -= varSize
                whichBlock = i
                break
        if (whichBlock == -1):
            return None
        tb.to_csv(self.TableBlockPath, index=False, sep=',') #找到空隙了，写入

        # blockDel = pd.read_csv(self.BlockDelPath)
        # temp = blockDel.blockAddr == whichBlock
        # for index, boolean in enumerate(temp):
        #     if (boolean == True):
        #         break
        # print(blockDel.iloc[index].delColumn)
        # blockDel.drop(index, inplace=True)
        # blockDel.to_csv(self.BlockDelPath, index=False, sep=',')

        with open(os.path.join(self.MemoryBlockPath, str(whichBlock) + ".csv"),"r+") as file:
            lines = file.readlines()
            file.seek(0, 2)
            lineNum = len(lines)
            file.write(",".join(varList) + "\n")
        return [os.path.join(self.MemoryBlockPath, str(whichBlock) + ".csv"),lineNum]

