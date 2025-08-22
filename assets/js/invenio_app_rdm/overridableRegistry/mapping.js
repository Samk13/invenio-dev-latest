// This file is part of InvenioRDM
// Copyright (C) 2023 CERN.
// Copyright (C) 2022-2025 KTH Royal Institute of Technology.
//
// Invenio App RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

/**
 * Add here all the overridden components of your app.
 */

import { RecommendedInformationOverride } from "../../components/deposit/overrides/CommunityHeaderOverride.js";
import { SubmitReviewModalComponent } from "../../components/deposit/SubmitReviewModalOverride.js";
import { PublishModalComponent } from "../../components/deposit/PublishModalOverride.js";

export const overriddenComponents = {
  "InvenioRdmRecords.SubmitReviewModal.container": SubmitReviewModalComponent,
  "InvenioRdmRecords.PublishModal.container": PublishModalComponent,
  "InvenioAppRdm.Deposit.CommunityHeader.container": () => null,
  "InvenioAppRdm.Deposit.AccordionFieldRecommendedInformation.container":
    RecommendedInformationOverride,
};
