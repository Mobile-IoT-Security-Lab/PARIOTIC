package models;

public abstract class CustomException extends RuntimeException {
    public CustomException(String message) {
        super(message);
    }

    public static class NoSourceSymbolException extends CustomException {

        public NoSourceSymbolException(String message) {
            super(message);
        }
    }
}
