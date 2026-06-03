import { GuidelineCatalog } from '@/types';

/**
 * Compute pre-formatted custom rule strings from locally-stored guideline
 * catalogs that are currently selected, filtered by workflow step and
 * excluding any individually deactivated rules.
 */
export function getCustomRulesForStep(
  customGuidelines: GuidelineCatalog[],
  selectedGuidelineIds: string[],
  excludedRuleIds: string[],
  step: string,
): string[] {
  const excluded = new Set(excludedRuleIds);
  const rules: string[] = [];

  for (const catalog of customGuidelines) {
    if (!selectedGuidelineIds.includes(catalog.id)) continue;
    for (const rule of catalog.rules || []) {
      if (excluded.has(rule.id)) continue;
      const applies = rule.applies_to || [];
      if (applies.length > 0 && !applies.includes(step)) continue;
      const v = (rule.verbindlichkeit || '').toUpperCase();
      const prefix = v ? `[${v}]` : '';
      rules.push(`${prefix} ${rule.rule}`);
    }
  }

  return rules;
}
