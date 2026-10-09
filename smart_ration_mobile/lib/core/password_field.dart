import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';

/// A password box with an eye button that shows or hides what was typed. Used for every password in the app,
/// so the button is never missing on one screen.
class PasswordFormField extends StatefulWidget {
  const PasswordFormField({
    super.key,
    required this.controller,
    required this.decoration,
    this.enabled = true,
    this.validator,
    this.autofillHints,
    this.maxLength,
    this.textInputAction,
    this.onFieldSubmitted,
  });

  final TextEditingController controller;
  final InputDecoration decoration;
  final bool enabled;
  final FormFieldValidator<String>? validator;
  final Iterable<String>? autofillHints;
  final int? maxLength;
  final TextInputAction? textInputAction;
  final ValueChanged<String>? onFieldSubmitted;

  @override
  State<PasswordFormField> createState() => _PasswordFormFieldState();
}

class _PasswordFormFieldState extends State<PasswordFormField> {
  bool _hidden = true;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return TextFormField(
      controller: widget.controller,
      enabled: widget.enabled,
      obscureText: _hidden,
      autocorrect: false,
      enableSuggestions: false,
      maxLength: widget.maxLength,
      autofillHints: widget.autofillHints,
      textInputAction: widget.textInputAction,
      onFieldSubmitted: widget.onFieldSubmitted,
      validator: widget.validator,
      decoration: widget.decoration.copyWith(
        suffixIcon: IconButton(
          icon: Icon(_hidden ? Icons.visibility_outlined : Icons.visibility_off_outlined),
          tooltip: _hidden ? l.showPassword : l.hidePassword,
          onPressed: () => setState(() => _hidden = !_hidden),
        ),
      ),
    );
  }
}
