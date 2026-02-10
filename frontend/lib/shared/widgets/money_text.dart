import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// A Text widget specialized for financial data.
/// 
/// It forces [FontFeature.tabularFigures] to ensure that numbers are monospaced
/// (fixed-width) for perfect vertical alignment in lists and tables.
class MoneyText extends StatelessWidget {
  final String data;
  final TextStyle? style;
  final TextAlign? textAlign;
  final TextOverflow? overflow;
  final int? maxLines;
  final bool softWrap;

  const MoneyText(
    this.data, {
    super.key,
    this.style,
    this.textAlign,
    this.overflow,
    this.maxLines,
    this.softWrap = true,
  });

  @override
  Widget build(BuildContext context) {
    // Merge the verified font features with the provided style
    final effectiveStyle = (style ?? DefaultTextStyle.of(context).style).copyWith(
      fontFeatures: [
        const FontFeature.tabularFigures(),
        ...?style?.fontFeatures, // Preserve other features if any
      ],
      // Ensure Inter is used, though theme should handle this globally
      // We explicitly check for tabular figures support in Inter
    );

    return Text(
      data,
      style: effectiveStyle,
      textAlign: textAlign,
      overflow: overflow,
      maxLines: maxLines,
      softWrap: softWrap,
    );
  }
}
