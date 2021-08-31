package models;

public class HexPlaceholder {
    private String source_file;
    private String original_function_name;
    private String new_function_name;
    private String hex_to_replace;

    public HexPlaceholder(String source_file, String original_function_name, String new_function_name, String hex_to_replace) {
        this.source_file = source_file;
        this.original_function_name = original_function_name;
        this.new_function_name = new_function_name;
        this.hex_to_replace = hex_to_replace;
    }

    public String getSource_file() {
        return source_file;
    }

    public String getOriginal_function_name() {
        return original_function_name;
    }

    public String getNew_function_name() {
        return new_function_name;
    }

    public String getHex_to_replace() {
        return hex_to_replace;
    }
}
