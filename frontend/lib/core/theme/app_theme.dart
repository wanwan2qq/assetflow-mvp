import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // M3 Seed Color - Deep Teal for Premium Fintech look
  // M3 Seed Color - Deep Teal for Premium Fintech look
  static const Color seedColor = Color(0xFF00695C); // Deep Teal 800

  // Semantic Colors
  static const Color incomeColorLight = Color(0xFF00695C);
  static const Color incomeColorDark = Color(0xFF80CBC4);
  static const Color expenseColorLight = Color(0xFFC62828); // Red 800
  static const Color expenseColorDark = Color(0xFFEF9A9A); // Red 200

  static const List<String> _fontFallbacks = [
    'PingFang SC',
    'Noto Sans SC',
    'Microsoft YaHei',
    'sans-serif',
  ];

  static TextTheme _buildTextTheme(TextTheme base) {
    // ... (rest of _buildTextTheme remains same, just ensuring context)
    // Apply Inter as the primary font with fallbacks for Chinese characters
    return GoogleFonts.interTextTheme(base).copyWith(
      displayLarge: GoogleFonts.inter(
        textStyle: base.displayLarge,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      displayMedium: GoogleFonts.inter(
        textStyle: base.displayMedium,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      displaySmall: GoogleFonts.inter(
        textStyle: base.displaySmall,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      headlineLarge: GoogleFonts.inter(
        textStyle: base.headlineLarge,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      headlineMedium: GoogleFonts.inter(
        textStyle: base.headlineMedium,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      headlineSmall: GoogleFonts.inter(
        textStyle: base.headlineSmall,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      titleLarge: GoogleFonts.inter(
        textStyle: base.titleLarge,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      titleMedium: GoogleFonts.inter(
        textStyle: base.titleMedium,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      titleSmall: GoogleFonts.inter(
        textStyle: base.titleSmall,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      bodyLarge: GoogleFonts.inter(
        textStyle: base.bodyLarge,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      bodyMedium: GoogleFonts.inter(
        textStyle: base.bodyMedium,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      bodySmall: GoogleFonts.inter(
        textStyle: base.bodySmall,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      labelLarge: GoogleFonts.inter(
        textStyle: base.labelLarge,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      labelMedium: GoogleFonts.inter(
        textStyle: base.labelMedium,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
      labelSmall: GoogleFonts.inter(
        textStyle: base.labelSmall,
      ).copyWith(fontFamilyFallback: _fontFallbacks),
    );
  }

  static ThemeData get lightTheme {
    final base = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: seedColor,
        brightness: Brightness.light,
      ),
      scaffoldBackgroundColor: const Color(0xFFFAFAFA), // Grey 50
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        backgroundColor: Colors.transparent,
        scrolledUnderElevation: 0,
      ),
      cardTheme: const CardThemeData(
        elevation: 0, // Flat cards for modern look
        color: Colors.white,
        margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),
    );
    
    return base.copyWith(
      textTheme: _buildTextTheme(base.textTheme),
    );
  }

  static ThemeData get darkTheme {
    final base = ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: seedColor,
        brightness: Brightness.dark,
        primary: const Color(0xFF80CBC4), // Teal 200 (Pastel)
        surface: const Color(0xFF121212), // Dark Background
        onSurface: const Color(0xFFEEEEEE), // Soft White
        surfaceContainerLow: const Color(0xFF1E1E1E), // Card Background
      ),
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        backgroundColor: Colors.transparent,
        scrolledUnderElevation: 0,
      ),
      cardTheme: const CardThemeData(
        elevation: 0,
        margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        color: Color(0xFF1E1E1E), // Card Background Level 1
      ),
      scaffoldBackgroundColor: const Color(0xFF121212), // Standard Dark Background
    );

    return base.copyWith(
      textTheme: _buildTextTheme(base.textTheme),
    );
  }
}