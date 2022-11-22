package models;

import java.util.List;

public class Symbol {
    // private static boolean getFromStart = true;
    public final int offset;
    public final String type;
    public final String name;
    public final  int length;
    public final String sourceFile;
    public Integer firstDataOffset = null;

    /**
     * Parse output of nm to a symbol instance
     * @param nmLine A line of output provided by nm
     */
    public Symbol(String nmLine, int textSectionAddr, int textSectionOffset, int relocationSectionAddr, int relocationSectionOffset) {
        String[] split = nmLine.trim().split("\\s+");
        if(split.length != 5) {
            throw new CustomException.NoSourceSymbolException("No source code symbol");
        }

        if (Integer.parseInt(split[0], 16) < relocationSectionAddr) {
            offset = Integer.parseInt(split[0], 16) - textSectionAddr + textSectionOffset;
        } else {
            offset = Integer.parseInt(split[0], 16) - relocationSectionAddr + relocationSectionOffset;
        }
        length = Integer.parseInt(split[1], 16);
        type = split[2];
        name = split[3];
        sourceFile = split[4].split(":")[0];
    }

    @Override
    public String toString() {
        return String.format("offset: %d, type: %s, name: %s", offset, type, name);
    }

    public int getSize() {
        if (this.firstDataOffset == null) {
            return this.length;
        }
        return (this.firstDataOffset - this.offset) + 1;
    }
}

