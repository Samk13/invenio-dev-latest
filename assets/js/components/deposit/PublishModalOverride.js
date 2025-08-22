// This file is part of InvenioRDM
// Copyright (C) 2023-2025 CERN.
// Copyright (C) 2022-2025 KTH Royal Institute of Technology.
//
// Invenio App RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

import React from "react";
import { PublishModal } from "@js/invenio_rdm_records";
import { parametrize } from "react-overridable";
import { TermsAndConditionsText } from "./TermsAndConditionsText.js";

const parameters = {
  extraCheckboxes: [
    {
      fieldPath: "acceptTermsOfService",
      text: <TermsAndConditionsText context="publish" />,
    },
  ],
};

export const PublishModalComponent = parametrize(PublishModal, parameters);
