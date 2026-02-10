import 'package:flutter/material.dart';
import '../../../../core/models/asset.dart';
import 'asset_forms/real_estate_form.dart';
import 'asset_forms/liability_form.dart';
import 'asset_forms/investment_form.dart';
import 'asset_forms/insurance_form.dart';
import 'asset_forms/cash_account_form.dart';

class AssetCreationSheet extends StatelessWidget {
  final AssetType initialType;

  const AssetCreationSheet({super.key, required this.initialType});

  @override
  Widget build(BuildContext context) {
    Widget form = const SizedBox();

    switch (initialType) {
      case AssetType.realEstate:
        form = const RealEstateForm();
        break;
      case AssetType.liability:
        form = const LiabilityForm();
        break;
      case AssetType.investment:
        form = const InvestmentForm();
        break;
      case AssetType.insurance:
        form = const InsuranceForm();
        break;
      case AssetType.cash:
        form = const CashAccountForm();
        break;
    }

    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Container(
      height: MediaQuery.of(context).size.height * 0.9,
      decoration: BoxDecoration(
        color: colorScheme.surfaceContainer,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: ClipRRect(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
        child: form
      ),
    );
  }
}
