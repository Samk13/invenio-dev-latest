// This file is part of InvenioRDM
// Copyright (C) 2023-2025 CERN.
// Copyright (C) 2022-2025 KTH Royal Institute of Technology.
//
// Invenio App RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import PropTypes from "prop-types";
import { getLocale } from "./utils";

// Terms and conditions messages for different contexts
const TERMS_MESSAGES = {
  publish: {
    en: "By publishing records, you hereby acknowledge and agree to be bound by the",
    sv: "Genom att publicera poster bekräftar du härmed och samtycker till att vara bunden av",
  },
  submit: {
    en: "By submitting records to our community, you hereby acknowledge and agree to be bound by the",
    sv: "Genom att skicka in poster till vår community bekräftar du härmed och samtycker till att vara bunden av",
  },
  join: {
    en: "By joining this community, you hereby acknowledge and agree to be bound by the",
    sv: "Genom att gå med i denna community bekräftar du härmed och samtycker till att vara bunden av",
  },
  invite: {
    en: "By accepting this invitation, you hereby acknowledge and agree to be bound by the",
    sv: "Genom att acceptera denna inbjudan bekräftar du härmed och samtycker till att vara bunden av",
  },
  default: {
    en: "By proceeding, you hereby acknowledge and agree to be bound by the",
    sv: "Genom att fortsätta bekräftar du härmed och samtycker till att vara bunden av",
  },
};

const LINK_TEXT = {
  en: "terms and conditions of service",
  sv: "användarvillkor och tjänstevillkor",
};

const ENDING_TEXT = {
  en: "as set forth by KTH Royal Institute of Technology.",
  sv: "som fastställts av KTH Kungliga Tekniska Högskolan.",
};

const TERMS_URL = {
  en: "https://docs.datarepository.kth.se/terms/",
  sv: "https://docs.datarepository.kth.se/sv/terms/",
};

const getCurrentLocaleMessage = (messages, locale) =>
  messages[locale] || messages["en"];

export const TermsAndConditionsText = ({ context = "submit" }) => {
  const locale = getLocale();

  const getContextText = (contextType) => {
    const messages = TERMS_MESSAGES[contextType] || TERMS_MESSAGES.default;
    return getCurrentLocaleMessage(messages, locale);
  };

  const termsUrl = getCurrentLocaleMessage(TERMS_URL, locale);
  const endingText = getCurrentLocaleMessage(ENDING_TEXT, locale);
  const linkText = getCurrentLocaleMessage(LINK_TEXT, locale);

  return (
    <>
      {getContextText(context)}{" "}
      <a rel="noopener noreferrer" href={termsUrl} target="_blank">
        {linkText}
      </a>{" "}
      {endingText}
    </>
  );
};

TermsAndConditionsText.propTypes = {
  context: PropTypes.oneOf(["submit", "publish", "join", "invite"]),
};

TermsAndConditionsText.defaultProps = {
  context: "submit",
};
