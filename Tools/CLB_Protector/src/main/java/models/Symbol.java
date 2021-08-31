package models;

import java.util.List;

public class Symbol {
    private static boolean getFromStart = true;
    public final int offset;
    public final String type;
    public final String name;
    public final  int length;
    public final String sourceFile;
    public int startOffsetIntegrityCheck;
    public int countOfIntegrityBytes;

    /**
     * Parse output of nm to a symbol instance
     * @param nmLine A line of output provided by nm
     */
    public Symbol(String nmLine) {
        String[] split = nmLine.trim().split("\\s+");
        if(split.length != 5) {
            throw new CustomException.NoSourceSymbolException("No source code symbol");
        }

        offset = Integer.parseInt(split[0], 16);
        length = Integer.parseInt(split[1], 16);
        type = split[2];
        name = split[3];
        sourceFile = split[4].split(":")[0];
    }

    public void computeIntegrityCheckRange(List<Symbol> newSymbols, int numberOfBytesOfElf) {
        if (getFromStart) {
            startOffsetIntegrityCheck = 0;
            countOfIntegrityBytes = newSymbols.get(0).offset;
        } else {
            startOffsetIntegrityCheck =
                    newSymbols.get(newSymbols.size() - 1).offset + newSymbols.get(newSymbols.size() - 1).length;
            countOfIntegrityBytes = numberOfBytesOfElf - startOffsetIntegrityCheck;
        }

        getFromStart = !getFromStart;
    }

    @Override
    public String toString() {
        return String.format("offset: %d, type: %s, name: %s", offset, type, name);
    }
}

