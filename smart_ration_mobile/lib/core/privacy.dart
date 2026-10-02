/// Checks for personal numbers that must never be typed into free-text fields (notes, complaints).
/// The backend checks again; this only lets the app explain the problem before sending anything.
library;

/// Twelve digits, with or without spaces or dashes: looks like an Aadhaar number.
final aadhaarLikePattern = RegExp(r'(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)');
