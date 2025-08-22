// This file is part of InvenioRDM
// Copyright (C) 2025 KTH Royal Institute of Technology.
//
// Invenio App RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

/**
 * Utility functions for locale handling
 */

/**
 * Get the current locale from document html lang attribute or default to 'en'
 * @returns {string} The current locale (e.g., 'en', 'sv')
 */
export const getLocale = () => {
  return document.documentElement.lang || "en";
};

/**
 * Get the appropriate message for the current locale with fallback to English
 * @param {Object} messages - Object with locale keys and message values
 * @param {string} locale - The target locale
 * @returns {string} The localized message
 */
export const getCurrentLocaleMessage = (messages, locale) =>
  messages[locale] || messages["en"];
